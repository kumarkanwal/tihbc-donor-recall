"""Conditional date, slot, and decline-reason extraction."""

import json
from typing import Literal

from app.agents.llm.router import get_structured_llm
from app.agents.nodes.schemas import StrictOutputModel
from app.agents.prompts import load_prompt
from app.agents.resolution import resolve_offered_slot, resolve_requested_date
from app.agents.state import ReplyState
from app.models.enums import DeclineReason, ResponseIntent


class RescheduleExpression(StrictOutputModel):
    """Exact reschedule expression extracted without resolving its value."""

    expression: str


class DeclineDetails(StrictOutputModel):
    """Structured decline reason."""

    decline_reason: Literal[
        "travelling",
        "health",
        "recently_donated",
        "not_interested",
        "other",
        "none",
    ]


async def extract_details(state: ReplyState) -> dict[str, object]:
    """Extract only the details relevant to the classified intent."""
    if state["intent"] == ResponseIntent.DECLINE:
        return await _decline_details(state)
    return await _reschedule_details(state)


async def _reschedule_details(state: ReplyState) -> dict[str, object]:
    existing_date = state.get("requested_date")
    existing_slot = state.get("selected_slot_id")
    if existing_date is not None or existing_slot is not None:
        return {"requested_date": existing_date, "selected_slot_id": existing_slot}
    context = {
        "text": state["text"],
        "awaiting": state["awaiting"],
        "offered_slots": [slot.label for slot in state["offered_slots"]],
    }
    prompt = load_prompt("extract_date.md").format(context=json.dumps(context, ensure_ascii=False))
    result = await get_structured_llm(RescheduleExpression).ainvoke(prompt)
    expression = "" if result.expression == "none" else result.expression
    selected = None
    if state["awaiting"] == "slot_choice":
        selected = resolve_offered_slot(expression, state["offered_slots"])
    return {
        "requested_date": resolve_requested_date(expression, state["today"]),
        "selected_slot_id": selected.id if selected is not None else None,
    }


async def _decline_details(state: ReplyState) -> dict[str, object]:
    prompt = load_prompt("extract_decline_reason.md").format(
        reply=json.dumps(
            {"text": state["text"], "detected_language": state["detected_language"]},
            ensure_ascii=False,
        )
    )
    result: DeclineDetails = await get_structured_llm(DeclineDetails).ainvoke(prompt)
    reason = None if result.decline_reason == "none" else DeclineReason(result.decline_reason)
    return {"decline_reason": reason}
