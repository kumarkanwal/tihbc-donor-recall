"""Real-provider evaluation set for the reply agent."""

from dataclasses import dataclass
from typing import Literal

from app.agents.state import AwaitingContext
from app.models.enums import DeclineReason, ResponseIntent


@dataclass(frozen=True)
class EvaluationCase:
    """One expected intent and optional extraction assertion."""

    text: str
    expected_intent: ResponseIntent
    awaiting: AwaitingContext = "none"
    expected_reason: DeclineReason | None = None
    date_offset_days: int | None = None
    next_weekday: int | None = None
    selected_slot_index: Literal[0, 1, 2] | None = None


EVALUATION_CASES = (
    EvaluationCase("Yes I will come", ResponseIntent.CONFIRM),
    EvaluationCase("Ji main aaunga", ResponseIntent.CONFIRM),
    EvaluationCase("میں آؤں گا", ResponseIntent.CONFIRM),
    EvaluationCase("Kal nahi, Monday ko aa sakta hoon", ResponseIntent.RESCHEDULE, next_weekday=0),
    EvaluationCase("Can we do next week?", ResponseIntent.RESCHEDULE, date_offset_days=7),
    EvaluationCase(
        "Main shehar se bahar hoon",
        ResponseIntent.DECLINE,
        expected_reason=DeclineReason.TRAVELLING,
    ),
    EvaluationCase(
        "Tabiyat theek nahi", ResponseIntent.DECLINE, expected_reason=DeclineReason.HEALTH
    ),
    EvaluationCase(
        "Abhi 1 mahina pehle diya tha",
        ResponseIntent.DECLINE,
        expected_reason=DeclineReason.RECENTLY_DONATED,
    ),
    EvaluationCase("Where is the center?", ResponseIntent.QUESTION),
    EvaluationCase("2nd wala", ResponseIntent.RESCHEDULE, "slot_choice", selected_slot_index=1),
    EvaluationCase("asdfgh", ResponseIntent.UNKNOWN),
    EvaluationCase("I can make it", ResponseIntent.CONFIRM),
    EvaluationCase("Haan zaroor aaunga", ResponseIntent.CONFIRM),
    EvaluationCase("جی ضرور", ResponseIntent.CONFIRM),
    EvaluationCase("Yes, see you there", ResponseIntent.CONFIRM),
    EvaluationCase("Tomorrow works better", ResponseIntent.RESCHEDULE, date_offset_days=1),
    EvaluationCase("Parson aa sakta hoon", ResponseIntent.RESCHEDULE, date_offset_days=2),
    EvaluationCase("Can I come Friday?", ResponseIntent.RESCHEDULE, next_weekday=4),
    EvaluationCase("اگلے ہفتے آ سکتا ہوں", ResponseIntent.RESCHEDULE, date_offset_days=7),
    EvaluationCase(
        "First one please", ResponseIntent.RESCHEDULE, "slot_choice", selected_slot_index=0
    ),
    EvaluationCase(
        "Saturday wala", ResponseIntent.RESCHEDULE, "slot_choice", selected_slot_index=1
    ),
    EvaluationCase(
        "I am out of Karachi",
        ResponseIntent.DECLINE,
        expected_reason=DeclineReason.TRAVELLING,
    ),
    EvaluationCase(
        "Doctor said I should not donate",
        ResponseIntent.DECLINE,
        expected_reason=DeclineReason.HEALTH,
    ),
    EvaluationCase(
        "Blood last month donate kiya",
        ResponseIntent.DECLINE,
        expected_reason=DeclineReason.RECENTLY_DONATED,
    ),
    EvaluationCase(
        "No thanks, I am not interested",
        ResponseIntent.DECLINE,
        expected_reason=DeclineReason.NOT_INTERESTED,
    ),
    EvaluationCase("سفر میں ہوں", ResponseIntent.DECLINE, expected_reason=DeclineReason.TRAVELLING),
    EvaluationCase("What time do you close?", ResponseIntent.QUESTION),
    EvaluationCase("Center ka address kya hai?", ResponseIntent.QUESTION),
    EvaluationCase("مرکز کا وقت کیا ہے؟", ResponseIntent.QUESTION),
    EvaluationCase("maybe", ResponseIntent.UNKNOWN),
    EvaluationCase(".", ResponseIntent.UNKNOWN),
)
