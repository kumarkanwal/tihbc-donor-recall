"""Multilingual graph examples, fallback safety, and PII boundaries."""

from contextlib import AbstractContextManager, nullcontext
from datetime import UTC, date, datetime, timedelta
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from app.agents.graph import ReplyAgent
from app.agents.llm.providers import EnabledProvider
from app.agents.llm.router import LLMRouter
from app.agents.state import AgentMetadata, AwaitingContext, OfferedSlot
from app.models.enums import DeclineReason, ResponseIntent
from tests.agents.fakes import CircuitStore, router_settings

TODAY = date(2026, 10, 5)
SLOT_IDS = (uuid4(), uuid4(), uuid4())


class SmartInvoker:
    """Return deterministic structured values while recording safe prompts."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def __call__(
        self, provider: EnabledProvider, schema: type[BaseModel], prompt: str
    ) -> BaseModel:
        del provider
        self.prompts.append(prompt)
        reply_context = prompt.strip().rsplit("\n", maxsplit=1)[-1].casefold()
        values = self._values(schema.__name__, reply_context)
        return schema.model_validate(values)

    def _values(self, schema_name: str, prompt: str) -> dict[str, object]:
        if schema_name == "LanguageOutput":
            roman = any(
                term in prompt
                for term in ("ji main", "kal nahi", "shehar", "tabiyat", "mahina", "wala")
            )
            return {"detected_language": "roman_ur" if roman else "en"}
        if schema_name == "IntentOutput":
            return {"intent": self._intent(prompt), "confidence": 0.98}
        if schema_name == "RescheduleExpression":
            return self._reschedule(prompt)
        return {"decline_reason": self._decline_reason(prompt)}

    @staticmethod
    def _intent(prompt: str) -> str:
        if "asdfgh" in prompt:
            return "unknown"
        if "where is the center" in prompt:
            return "question"
        if any(term in prompt for term in ("kal nahi", "next week", "2nd wala")):
            return "reschedule"
        if any(term in prompt for term in ("shehar se bahar", "tabiyat", "mahina pehle")):
            return "decline"
        return "confirm"

    @staticmethod
    def _reschedule(prompt: str) -> dict[str, object]:
        if "2nd wala" in prompt:
            return {"expression": "2nd wala"}
        if "next week" in prompt or "monday ko" in prompt:
            return {"expression": "next week"}
        return {"expression": "none"}

    @staticmethod
    def _decline_reason(prompt: str) -> str:
        if "shehar se bahar" in prompt:
            return "travelling"
        if "tabiyat" in prompt:
            return "health"
        if "mahina pehle" in prompt:
            return "recently_donated"
        return "other"


class LowConfidenceInvoker(SmartInvoker):
    """Return a structurally valid classification below the safety threshold."""

    def _values(self, schema_name: str, prompt: str) -> dict[str, object]:
        values = super()._values(schema_name, prompt)
        if schema_name == "IntentOutput":
            values["confidence"] = 0.4
        return values


def _slots() -> list[OfferedSlot]:
    return [
        OfferedSlot(
            id=slot_id,
            starts_at=datetime(2026, 10, 6 + index, 7, tzinfo=UTC),
            center_name="Korangi Campus Blood Center",
            label=f"Option {index + 1}",
        )
        for index, slot_id in enumerate(SLOT_IDS)
    ]


def _agent(invoker: SmartInvoker, *, tracing_enabled: bool = False) -> ReplyAgent:
    router = LLMRouter(
        router_settings(llm_provider_order=("groq",)), CircuitStore(), provider_invoker=invoker
    )
    return ReplyAgent(
        router,
        confidence_threshold=0.7,
        tracing_enabled=tracing_enabled,
        langsmith_api_key="langsmith-secret" if tracing_enabled else None,
        langsmith_project="tests",
        langsmith_endpoint="https://api.smith.langchain.com",
    )


def _metadata(awaiting: AwaitingContext = "none") -> AgentMetadata:
    return AgentMetadata(
        campaign_id=uuid4(),
        enrollment_id=uuid4(),
        donor_language="en",
        awaiting=awaiting,
        environment="test",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "awaiting", "intent", "requested_date", "reason", "slot_id"),
    [
        ("Yes I will come", "none", ResponseIntent.CONFIRM, None, None, None),
        ("Ji main aaunga", "none", ResponseIntent.CONFIRM, None, None, None),
        ("میں آؤں گا", "none", ResponseIntent.CONFIRM, None, None, None),
        (
            "Kal nahi, Monday ko aa sakta hoon",
            "none",
            ResponseIntent.RESCHEDULE,
            date(2026, 10, 12),
            None,
            None,
        ),
        (
            "Can we do next week?",
            "none",
            ResponseIntent.RESCHEDULE,
            TODAY + timedelta(days=7),
            None,
            None,
        ),
        (
            "Main shehar se bahar hoon",
            "none",
            ResponseIntent.DECLINE,
            None,
            DeclineReason.TRAVELLING,
            None,
        ),
        (
            "Tabiyat theek nahi",
            "none",
            ResponseIntent.DECLINE,
            None,
            DeclineReason.HEALTH,
            None,
        ),
        (
            "Abhi 1 mahina pehle diya tha",
            "none",
            ResponseIntent.DECLINE,
            None,
            DeclineReason.RECENTLY_DONATED,
            None,
        ),
        ("Where is the center?", "none", ResponseIntent.QUESTION, None, None, None),
        ("2nd wala", "slot_choice", ResponseIntent.RESCHEDULE, None, None, SLOT_IDS[1]),
        ("asdfgh", "none", ResponseIntent.UNKNOWN, None, None, None),
    ],
)
async def test_documented_agent_examples(
    text: str,
    awaiting: AwaitingContext,
    intent: ResponseIntent,
    requested_date: date | None,
    reason: DeclineReason | None,
    slot_id: UUID | None,
) -> None:
    invoker = SmartInvoker()
    agent = _agent(invoker)

    result = await agent.run(
        text=text,
        donor_language="ur" if "آ" in text else "en",
        awaiting=awaiting,
        offered_slots=_slots(),
        today=TODAY,
        metadata=_metadata(awaiting),
    )

    assert result.intent == intent
    assert result.requested_date == requested_date
    assert result.decline_reason == reason
    assert result.selected_slot_id == slot_id


@pytest.mark.asyncio
async def test_all_provider_failures_return_unknown() -> None:
    router = LLMRouter(router_settings(llm_provider_order=()), CircuitStore())
    agent = ReplyAgent(
        router,
        confidence_threshold=0.7,
        tracing_enabled=False,
        langsmith_api_key=None,
        langsmith_project="tests",
        langsmith_endpoint="https://api.smith.langchain.com",
    )

    result = await agent.run(
        text="Yes I will come",
        donor_language="en",
        awaiting="none",
        offered_slots=[],
        today=TODAY,
        metadata=_metadata(),
    )

    assert result.intent == ResponseIntent.UNKNOWN
    assert result.confidence == 0


@pytest.mark.asyncio
async def test_low_confidence_is_forced_to_unknown() -> None:
    result = await _agent(LowConfidenceInvoker()).run(
        text="Yes I will come",
        donor_language="en",
        awaiting="none",
        offered_slots=[],
        today=TODAY,
        metadata=_metadata(),
    )

    assert result.intent == ResponseIntent.UNKNOWN
    assert result.confidence == 0.4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "awaiting", "requested_date", "slot_id"),
    [
        ("Parson aa sakta hoon", "none", date(2026, 10, 7), None),
        ("Friday", "none", date(2026, 10, 9), None),
        ("first one", "slot_choice", None, SLOT_IDS[0]),
        ("2nd wala", "slot_choice", None, SLOT_IDS[1]),
    ],
)
async def test_deterministic_reschedules_do_not_call_a_provider(
    text: str,
    awaiting: AwaitingContext,
    requested_date: date | None,
    slot_id: UUID | None,
) -> None:
    invoker = SmartInvoker()

    result = await _agent(invoker).run(
        text=text,
        donor_language="en",
        awaiting=awaiting,
        offered_slots=_slots(),
        today=TODAY,
        metadata=_metadata(awaiting),
    )

    assert result.intent == ResponseIntent.RESCHEDULE
    assert result.requested_date == requested_date
    assert result.selected_slot_id == slot_id
    assert invoker.prompts == []


@pytest.mark.asyncio
async def test_maybe_is_unknown_without_intent_model_call() -> None:
    invoker = SmartInvoker()

    result = await _agent(invoker).run(
        text="maybe",
        donor_language="en",
        awaiting="none",
        offered_slots=[],
        today=TODAY,
        metadata=_metadata(),
    )

    assert result.intent == ResponseIntent.UNKNOWN
    assert len(invoker.prompts) == 1


class CapturedRun(AbstractContextManager["CapturedRun"]):
    """Capture root trace inputs, metadata, and tags without network calls."""

    trace_id = uuid4()

    def __init__(self, values: dict[str, object], **kwargs: object) -> None:
        self.values = values
        self.values.update(kwargs)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback

    def add_metadata(self, metadata: dict[str, object]) -> None:
        self.values["final_metadata"] = metadata

    def add_tags(self, tags: list[str]) -> None:
        self.values["tags"] = tags

    def end(self, *, outputs: dict[str, object]) -> None:
        self.values["outputs"] = outputs


@pytest.mark.asyncio
async def test_prompts_and_trace_metadata_exclude_phone_and_donor_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoker = SmartInvoker()
    captured: dict[str, object] = {}

    def fake_trace(name: str, **kwargs: object) -> CapturedRun:
        captured["name"] = name
        return CapturedRun(captured, **kwargs)

    monkeypatch.setattr("app.agents.graph.trace", fake_trace)
    monkeypatch.setattr("app.agents.graph.Client", lambda **kwargs: object())
    monkeypatch.setattr("app.agents.graph.tracing_context", lambda **kwargs: nullcontext())
    result = await _agent(invoker, tracing_enabled=True).run(
        text="Please call +923001234567, yes I will come",
        donor_language="en",
        awaiting="none",
        offered_slots=[],
        today=TODAY,
        metadata=_metadata(),
    )

    serialized = repr((captured, invoker.prompts))
    assert result.intent == ResponseIntent.CONFIRM
    assert "+923001234567" not in serialized
    assert "Test Donor" not in serialized
    assert "[phone]" in serialized
    assert captured["name"] == "donor_reply"
    assert result.trace_id == str(CapturedRun.trace_id)
    metadata = captured["final_metadata"]
    assert isinstance(metadata, dict)
    assert metadata["llm_provider"] == "groq"
    assert metadata["fallback_count"] == 0
    assert captured["tags"] == ["intent:confirm", "source:agent", "fallback:false"]
