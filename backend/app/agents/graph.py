"""Compiled LangGraph reply agent with PII-safe LangSmith tracing."""

from collections.abc import Mapping
from datetime import date
from typing import Literal, cast

import structlog
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langsmith import Client
from langsmith.run_helpers import trace, tracing_context

from app.agents.fallback import classify_fallback
from app.agents.llm.router import LLMRouter, RouteStats, RoutingUnavailable, routing_context
from app.agents.nodes.build_result import build_result
from app.agents.nodes.classify_intent import classify_intent
from app.agents.nodes.detect_language import detect_language
from app.agents.nodes.extract_details import extract_details
from app.agents.privacy import sanitize_reply_text
from app.agents.state import (
    AgentExecution,
    AgentFailure,
    AgentMetadata,
    AgentResult,
    AwaitingContext,
    OfferedSlot,
    ReplyState,
)
from app.models.enums import ResponseIntent

logger = structlog.get_logger(__name__)


def _detail_route(state: ReplyState) -> Literal["extract_details", "build_result"]:
    if state["intent"] in {ResponseIntent.RESCHEDULE, ResponseIntent.DECLINE}:
        return "extract_details"
    return "build_result"


def build_graph() -> CompiledStateGraph[ReplyState, None, ReplyState, ReplyState]:
    """Compile the stateless reply-classification graph."""
    workflow = StateGraph(ReplyState)
    workflow.add_node("detect_language", detect_language)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("extract_details", extract_details)
    workflow.add_node("build_result", build_result)
    workflow.add_edge(START, "detect_language")
    workflow.add_edge("detect_language", "classify_intent")
    workflow.add_conditional_edges("classify_intent", _detail_route)
    workflow.add_edge("extract_details", "build_result")
    workflow.add_edge("build_result", END)
    return workflow.compile()


class ReplyAgent:
    """Run the reply graph and convert every provider failure to unknown."""

    def __init__(
        self,
        router: LLMRouter,
        *,
        confidence_threshold: float,
        tracing_enabled: bool,
        langsmith_api_key: str | None,
        langsmith_project: str,
        langsmith_endpoint: str,
    ) -> None:
        self._router = router
        self._confidence_threshold = confidence_threshold
        self._graph = build_graph()
        self._tracing_enabled = tracing_enabled
        self._project = langsmith_project
        self._client = (
            Client(api_url=langsmith_endpoint, api_key=langsmith_api_key)
            if tracing_enabled and langsmith_api_key
            else None
        )

    async def run(
        self,
        *,
        text: str,
        donor_language: Literal["en", "ur"],
        awaiting: AwaitingContext,
        offered_slots: list[OfferedSlot],
        today: date,
        metadata: AgentMetadata,
    ) -> AgentResult:
        """Return only the documented public agent result."""
        execution = await self.run_with_diagnostics(
            text=text,
            donor_language=donor_language,
            awaiting=awaiting,
            offered_slots=offered_slots,
            today=today,
            metadata=metadata,
        )
        return execution.result

    async def run_with_diagnostics(
        self,
        *,
        text: str,
        donor_language: Literal["en", "ur"],
        awaiting: AwaitingContext,
        offered_slots: list[OfferedSlot],
        today: date,
        metadata: AgentMetadata,
    ) -> AgentExecution:
        """Run the graph and retain non-secret provider diagnostics."""
        safe_text = sanitize_reply_text(text)
        state = _initial_state(
            safe_text,
            donor_language,
            awaiting,
            offered_slots,
            today,
            self._confidence_threshold,
        )
        async with routing_context(self._router) as route:
            return await self._run_traced(state, metadata, route)

    async def _run_traced(
        self, state: ReplyState, metadata: AgentMetadata, route: RouteStats
    ) -> AgentExecution:
        initial_metadata = _trace_metadata(metadata, route)
        inputs = _trace_inputs(state)
        with (
            tracing_context(
                enabled=self._tracing_enabled,
                project_name=self._project,
                client=self._client,
            ),
            trace(
                "donor_reply",
                inputs=inputs,
                metadata=initial_metadata,
                project_name=self._project,
                client=self._client,
            ) as run,
        ):
            result, failure = await self._safe_invoke(state)
            if failure is not None:
                route.provider = None
                route.model = None
            run.add_metadata(_trace_metadata(metadata, route))
            run.add_tags(
                [
                    f"intent:{result.intent.value}",
                    "source:agent",
                    f"fallback:{str(failure is not None or route.fallback_count > 0).lower()}",
                ]
            )
            run.end(outputs={"intent": result.intent.value, "confidence": result.confidence})
            trace_id = str(run.trace_id) if self._tracing_enabled else None
        traced_result = result.model_copy(update={"trace_id": trace_id})
        return AgentExecution(
            result=traced_result,
            provider=route.provider,
            model=route.model,
            fallback_count=route.fallback_count,
            attempts=tuple(route.attempts),
            failure=failure,
        )

    async def _safe_invoke(self, state: ReplyState) -> tuple[AgentResult, AgentFailure | None]:
        try:
            raw = await self._graph.ainvoke(state)
            result = cast(Mapping[str, object], raw).get("result")
            if not isinstance(result, AgentResult):
                raise RoutingUnavailable("Agent graph returned no result")
            return result, None
        except Exception as error:
            logger.warning("reply_agent_fallback", error_type=type(error).__name__)
            fallback = classify_fallback(
                state["text"],
                today=state["today"],
                awaiting=state["awaiting"],
                offered_slot_ids=tuple(slot.id for slot in state["offered_slots"]),
            )
            return (
                AgentResult(
                    intent=ResponseIntent.UNKNOWN,
                    confidence=0,
                    detected_language=fallback.detected_language,
                ),
                ("routing_unavailable" if isinstance(error, RoutingUnavailable) else "agent_error"),
            )


def _initial_state(
    text: str,
    donor_language: Literal["en", "ur"],
    awaiting: AwaitingContext,
    offered_slots: list[OfferedSlot],
    today: date,
    confidence_threshold: float,
) -> ReplyState:
    return {
        "text": text,
        "donor_language": donor_language,
        "awaiting": awaiting,
        "offered_slots": offered_slots,
        "today": today,
        "confidence_threshold": confidence_threshold,
    }


def _trace_inputs(state: ReplyState) -> dict[str, object]:
    return {
        "text": state["text"],
        "donor_language": state["donor_language"],
        "awaiting": state["awaiting"],
        "offered_slots": [slot.model_dump(mode="json") for slot in state["offered_slots"]],
        "today": state["today"].isoformat(),
    }


def _trace_metadata(metadata: AgentMetadata, route: RouteStats) -> dict[str, object]:
    return {
        "campaign_id": str(metadata.campaign_id),
        "enrollment_id": str(metadata.enrollment_id),
        "donor_language": metadata.donor_language,
        "awaiting": metadata.awaiting,
        "environment": metadata.environment,
        "llm_provider": route.provider or "none",
        "llm_model": route.model or "none",
        "fallback_count": route.fallback_count,
    }
