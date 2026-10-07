"""Structured reply-intent classification node."""

import json

from pydantic import Field

from app.agents.llm.router import get_structured_llm
from app.agents.nodes.schemas import StrictOutputModel
from app.agents.prompts import load_prompt
from app.agents.resolution import (
    is_ambiguous_reply,
    resolve_offered_slot,
    resolve_requested_date,
)
from app.agents.state import ReplyState
from app.models.enums import ResponseIntent


class IntentOutput(StrictOutputModel):
    """Intent and confidence returned by an LLM provider."""

    intent: ResponseIntent
    confidence: float = Field(ge=0, le=1)


async def classify_intent(state: ReplyState) -> dict[str, object]:
    """Classify intent with the current deterministic conversation context."""
    deterministic = _deterministic_reschedule(state)
    if deterministic is not None:
        return deterministic
    if is_ambiguous_reply(state["text"]):
        return {"intent": ResponseIntent.UNKNOWN, "confidence": 1.0}
    context = {
        "text": state["text"],
        "detected_language": state["detected_language"],
        "awaiting": state["awaiting"],
        "offered_slots": [slot.model_dump(mode="json") for slot in state["offered_slots"]],
    }
    prompt = load_prompt("classify_intent.md").format(
        context=json.dumps(context, ensure_ascii=False)
    )
    result: IntentOutput = await get_structured_llm(IntentOutput).ainvoke(prompt)
    return {"intent": result.intent, "confidence": result.confidence}


def _deterministic_reschedule(state: ReplyState) -> dict[str, object] | None:
    if state["awaiting"] == "slot_choice":
        slot = resolve_offered_slot(state["text"], state["offered_slots"])
        if slot is not None:
            return {
                "intent": ResponseIntent.RESCHEDULE,
                "confidence": 1.0,
                "selected_slot_id": slot.id,
            }
    requested_date = resolve_requested_date(state["text"], state["today"])
    if requested_date is None:
        return None
    return {
        "intent": ResponseIntent.RESCHEDULE,
        "confidence": 1.0,
        "requested_date": requested_date,
    }
