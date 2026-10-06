"""Structured reply-intent classification node."""

import json

from pydantic import BaseModel, Field

from app.agents.llm.router import get_structured_llm
from app.agents.prompts import load_prompt
from app.agents.state import ReplyState
from app.models.enums import ResponseIntent


class IntentOutput(BaseModel):
    """Intent and confidence returned by an LLM provider."""

    intent: ResponseIntent
    confidence: float = Field(ge=0, le=1)


async def classify_intent(state: ReplyState) -> dict[str, object]:
    """Classify intent with the current deterministic conversation context."""
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
