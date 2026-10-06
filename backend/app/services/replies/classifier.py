"""Button, fallback, and LangGraph classification orchestration."""

from datetime import date
from typing import Literal, Protocol
from uuid import UUID

import structlog

from app.agents.state import AgentMetadata, AgentResult, AwaitingContext, OfferedSlot
from app.core.clock import Clock
from app.models.campaign import Enrollment
from app.models.donor import Donor
from app.models.enums import ResponseIntent
from app.models.message import Message
from app.repositories.appointment import AppointmentRepository
from app.schemas.simulator import ButtonReply, SimulatorReply
from app.services.replies.classification import (
    Classification,
    awaiting_context,
    classify_agent_result,
    classify_button_reply,
    classify_fallback_reply,
    offered_slot_ids,
)

logger = structlog.get_logger(__name__)


class ReplyAgentRunner(Protocol):
    """PII-safe agent boundary consumed by reply classification."""

    async def run(
        self,
        *,
        text: str,
        donor_language: Literal["en", "ur"],
        awaiting: AwaitingContext,
        offered_slots: list[OfferedSlot],
        today: date,
        metadata: AgentMetadata,
    ) -> AgentResult: ...


class ReplyClassifier:
    """Select deterministic or agent classification for one inbound reply."""

    def __init__(
        self,
        appointment_slots: AppointmentRepository,
        current_clock: Clock,
        *,
        llm_enabled: bool,
        agent: ReplyAgentRunner | None,
        environment: str,
        confidence_threshold: float,
    ) -> None:
        self._appointment_slots = appointment_slots
        self._clock = current_clock
        self._llm_enabled = llm_enabled
        self._agent = agent
        self._environment = environment
        self._confidence_threshold = confidence_threshold

    async def classify(
        self,
        request: SimulatorReply,
        source: Message,
        donor: Donor,
        enrollment: Enrollment,
    ) -> Classification:
        """Classify one validated reply without exposing donor identity to the agent."""
        if isinstance(request, ButtonReply):
            return classify_button_reply(request, source, donor)
        if not self._llm_enabled or self._agent is None:
            return classify_fallback_reply(
                request,
                source,
                donor,
                today=self._clock.now().date(),
                confidence_threshold=self._confidence_threshold,
            )
        awaiting = awaiting_context(source)
        result = await self._safe_agent_result(request, source, donor, enrollment, awaiting)
        return classify_agent_result(result, awaiting)

    async def _safe_agent_result(
        self,
        request: SimulatorReply,
        source: Message,
        donor: Donor,
        enrollment: Enrollment,
        awaiting: AwaitingContext,
    ) -> AgentResult:
        if isinstance(request, ButtonReply) or self._agent is None:
            raise AssertionError("Agent classification requires free text and an agent")
        try:
            return await self._agent.run(
                text=request.text,
                donor_language=donor.language.value,
                awaiting=awaiting,
                offered_slots=await self._agent_slots(source),
                today=self._clock.now().date(),
                metadata=AgentMetadata(
                    campaign_id=enrollment.campaign_id,
                    enrollment_id=enrollment.id,
                    donor_language=donor.language.value,
                    awaiting=awaiting,
                    environment=self._environment,
                ),
            )
        except Exception as error:
            logger.warning(
                "reply_agent_unavailable",
                enrollment_id=str(enrollment.id),
                error_type=type(error).__name__,
            )
            return AgentResult(
                intent=ResponseIntent.UNKNOWN,
                confidence=0,
                detected_language=donor.language.value,
            )

    async def _agent_slots(self, source: Message) -> list[OfferedSlot]:
        ids = offered_slot_ids(source)
        if not ids:
            return []
        slots = await self._appointment_slots.get_slots(ids)
        labels = _slot_labels(source)
        return [
            OfferedSlot(
                id=slot.id,
                starts_at=slot.starts_at,
                center_name=slot.center_name,
                label=labels.get(slot.id, ""),
            )
            for slot in slots
        ]


def _slot_labels(source: Message) -> dict[UUID, str]:
    return {
        slot_id: str(button.get("label", ""))
        for button in source.buttons or []
        if (slot_id := _button_slot_id(str(button.get("id", "")))) is not None
    }


def _button_slot_id(button_id: str) -> UUID | None:
    if not button_id.startswith("slot_"):
        return None
    try:
        return UUID(hex=button_id.removeprefix("slot_"))
    except ValueError:
        return None
