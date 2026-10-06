"""Map simulator buttons and fallback text into structured response results."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.agents.fallback import classify_fallback
from app.agents.state import AgentResult, AwaitingContext
from app.models.donor import Donor
from app.models.enums import DeclineReason, ResponseIntent, ResponseSource
from app.models.message import Message
from app.schemas.simulator import ButtonReply, SimulatorReply

BUTTON_INTENTS = {
    "btn_confirm": ResponseIntent.CONFIRM,
    "confirm": ResponseIntent.CONFIRM,
    "btn_reschedule": ResponseIntent.RESCHEDULE,
    "reschedule": ResponseIntent.RESCHEDULE,
    "btn_decline": ResponseIntent.DECLINE,
    "decline": ResponseIntent.DECLINE,
}
REASON_BUTTONS = {
    "btn_reason_travelling": DeclineReason.TRAVELLING,
    "btn_reason_health": DeclineReason.HEALTH,
    "btn_reason_other": DeclineReason.OTHER,
}
WEEKDAY_ALIASES = (
    (("monday", "mon", "peer"), ("mon", "پیر")),
    (("tuesday", "tue", "mangal"), ("tue", "منگل")),
    (("wednesday", "wed", "budh"), ("wed", "بدھ")),
    (("thursday", "thu", "jumeraat"), ("thu", "جمعرات")),
    (("friday", "fri", "jumma"), ("fri", "جمعہ")),
    (("saturday", "sat", "hafta"), ("sat", "ہفتہ")),
    (("sunday", "sun", "itwar"), ("sun", "اتوار")),
)


@dataclass(frozen=True)
class Classification:
    """Database-ready deterministic classification."""

    intent: ResponseIntent
    source: ResponseSource
    detected_language: str
    confidence: Decimal
    requested_date: date | None = None
    selected_slot_id: UUID | None = None
    decline_reason: DeclineReason | None = None
    awaiting: AwaitingContext = "none"
    trace_id: str | None = None


def classify_fallback_reply(
    request: SimulatorReply,
    source_message: Message,
    donor: Donor,
    *,
    today: date,
    confidence_threshold: float,
) -> Classification:
    """Classify a validated reply without external services."""
    if isinstance(request, ButtonReply):
        return classify_button_reply(request, source_message, donor)
    offered_slots = offered_slot_ids(source_message)
    awaiting = awaiting_context(source_message)
    result = classify_fallback(
        request.text,
        today=today,
        awaiting=awaiting,
        offered_slot_ids=offered_slots,
    )
    selected_slot = result.selected_slot_id or _weekday_slot(request.text, source_message)
    confidence = 0.9 if selected_slot is not None else result.confidence
    intent = (
        ResponseIntent.RESCHEDULE
        if selected_slot is not None
        else result.intent
        if confidence >= confidence_threshold
        else ResponseIntent.UNKNOWN
    )
    return Classification(
        intent=intent,
        source=ResponseSource.AGENT,
        detected_language=result.detected_language,
        confidence=Decimal(str(confidence)),
        requested_date=result.requested_date,
        selected_slot_id=selected_slot,
        decline_reason=result.decline_reason,
        awaiting=awaiting,
    )


def classify_agent_result(result: AgentResult, awaiting: AwaitingContext) -> Classification:
    """Convert the database-independent agent result for the reply flow."""
    return Classification(
        intent=result.intent,
        source=ResponseSource.AGENT,
        detected_language=result.detected_language,
        confidence=Decimal(str(result.confidence)),
        requested_date=result.requested_date,
        selected_slot_id=result.selected_slot_id,
        decline_reason=result.decline_reason,
        awaiting=awaiting,
        trace_id=result.trace_id,
    )


def classify_button_reply(
    request: ButtonReply, source_message: Message, donor: Donor
) -> Classification:
    """Map a validated button identifier directly without an LLM."""
    reason = REASON_BUTTONS.get(request.button_id)
    selected_slot = _slot_id(request.button_id)
    intent = BUTTON_INTENTS.get(request.button_id)
    if reason is not None:
        intent = ResponseIntent.DECLINE
    elif selected_slot is not None:
        intent = ResponseIntent.RESCHEDULE
    if intent is None:
        button = next(
            item for item in source_message.buttons or [] if item.get("id") == request.button_id
        )
        intent = ResponseIntent(str(button["intent"]))
    return Classification(
        intent=intent,
        source=ResponseSource.BUTTON,
        detected_language=donor.language.value,
        confidence=Decimal("1.00"),
        selected_slot_id=selected_slot,
        decline_reason=reason,
    )


def awaiting_context(source_message: Message) -> AwaitingContext:
    """Infer the pending deterministic question from source buttons."""
    button_ids = {str(item.get("id")) for item in source_message.buttons or []}
    if any(button_id.startswith("slot_") for button_id in button_ids):
        return "slot_choice"
    if button_ids & REASON_BUTTONS.keys():
        return "decline_reason"
    return "none"


def offered_slot_ids(source_message: Message) -> tuple[UUID, ...]:
    """Return appointment IDs encoded in the source message buttons."""
    return tuple(
        slot_id
        for button in source_message.buttons or []
        if (slot_id := _slot_id(str(button.get("id")))) is not None
    )


def _slot_id(button_id: str) -> UUID | None:
    if not button_id.startswith("slot_"):
        return None
    try:
        return UUID(hex=button_id.removeprefix("slot_"))
    except ValueError:
        return None


def _weekday_slot(text: str, source_message: Message) -> UUID | None:
    normalized = text.casefold()
    for aliases, label_markers in WEEKDAY_ALIASES:
        if not any(alias in normalized for alias in aliases):
            continue
        for button in source_message.buttons or []:
            label = str(button.get("label", "")).casefold()
            if any(marker in label for marker in label_markers):
                return _slot_id(str(button.get("id")))
    return None
