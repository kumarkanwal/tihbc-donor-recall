"""Conditional date, slot, and decline-reason extraction."""

import json
from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.agents.llm.router import get_structured_llm
from app.agents.prompts import load_prompt
from app.agents.state import ReplyState
from app.models.enums import DeclineReason, ResponseIntent


class RescheduleDetails(BaseModel):
    """Structured date and offered-slot selection."""

    requested_date: date | None
    selected_slot_id: UUID | None


class DeclineDetails(BaseModel):
    """Structured decline reason."""

    decline_reason: DeclineReason | None


async def extract_details(state: ReplyState) -> dict[str, object]:
    """Extract only the details relevant to the classified intent."""
    if state["intent"] == ResponseIntent.DECLINE:
        return await _decline_details(state)
    return await _reschedule_details(state)


async def _reschedule_details(state: ReplyState) -> dict[str, object]:
    context = {
        "text": state["text"],
        "today": state["today"].isoformat(),
        "awaiting": state["awaiting"],
        "offered_slots": [slot.model_dump(mode="json") for slot in state["offered_slots"]],
    }
    prompt = load_prompt("extract_date.md").format(context=json.dumps(context, ensure_ascii=False))
    result: RescheduleDetails = await get_structured_llm(RescheduleDetails).ainvoke(prompt)
    offered_ids = {slot.id for slot in state["offered_slots"]}
    selected = result.selected_slot_id if result.selected_slot_id in offered_ids else None
    return {"requested_date": result.requested_date, "selected_slot_id": selected}


async def _decline_details(state: ReplyState) -> dict[str, object]:
    prompt = load_prompt("extract_decline_reason.md").format(
        reply=json.dumps(
            {"text": state["text"], "detected_language": state["detected_language"]},
            ensure_ascii=False,
        )
    )
    result: DeclineDetails = await get_structured_llm(DeclineDetails).ainvoke(prompt)
    return {"decline_reason": result.decline_reason}
