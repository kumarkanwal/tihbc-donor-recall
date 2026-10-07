"""Rule-first donor reply language detection."""

import json
import re

from app.agents.llm.router import get_structured_llm
from app.agents.nodes.schemas import StrictOutputModel
from app.agents.prompts import load_prompt
from app.agents.resolution import (
    looks_roman_urdu,
    resolve_offered_slot,
    resolve_requested_date,
)
from app.agents.state import DetectedLanguage, ReplyState

URDU_SCRIPT = re.compile(r"[\u0600-\u06ff]")


class LanguageOutput(StrictOutputModel):
    """Structured Latin-script language distinction."""

    detected_language: DetectedLanguage


async def detect_language(state: ReplyState) -> dict[str, object]:
    """Detect Urdu script locally and ask the router only for Latin text."""
    if URDU_SCRIPT.search(state["text"]):
        return {"detected_language": "ur"}
    deterministic_reschedule = resolve_requested_date(state["text"], state["today"])
    deterministic_slot = None
    if state["awaiting"] == "slot_choice":
        deterministic_slot = resolve_offered_slot(state["text"], state["offered_slots"])
    if deterministic_reschedule is not None or deterministic_slot is not None:
        language: DetectedLanguage = "roman_ur" if looks_roman_urdu(state["text"]) else "en"
        return {"detected_language": language}
    prompt = load_prompt("detect_language.md").format(
        reply=json.dumps({"text": state["text"]}, ensure_ascii=False)
    )
    result: LanguageOutput = await get_structured_llm(LanguageOutput).ainvoke(prompt)
    language = result.detected_language
    if language == "ur":
        language = "roman_ur"
    return {"detected_language": language}
