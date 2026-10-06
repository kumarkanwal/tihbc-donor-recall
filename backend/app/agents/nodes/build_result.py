"""Final agent-result construction node."""

from app.agents.state import AgentResult, ReplyState
from app.models.enums import ResponseIntent


def build_result(state: ReplyState) -> dict[str, object]:
    """Apply the confidence guard and construct the public result."""
    confidence = state["confidence"]
    intent = state["intent"]
    if confidence < state["confidence_threshold"]:
        intent = ResponseIntent.UNKNOWN
    result = AgentResult(
        intent=intent,
        confidence=confidence,
        detected_language=state["detected_language"],
        requested_date=state.get("requested_date") if intent != ResponseIntent.UNKNOWN else None,
        selected_slot_id=(
            state.get("selected_slot_id") if intent != ResponseIntent.UNKNOWN else None
        ),
        decline_reason=state.get("decline_reason") if intent != ResponseIntent.UNKNOWN else None,
        trace_id=None,
    )
    return {"result": result}
