"""Rule-first donor reply language detection."""

import json
import re

from pydantic import BaseModel

from app.agents.llm.router import get_structured_llm
from app.agents.prompts import load_prompt
from app.agents.state import DetectedLanguage, ReplyState

URDU_SCRIPT = re.compile(r"[\u0600-\u06ff]")


class LanguageOutput(BaseModel):
    """Structured Latin-script language distinction."""

    detected_language: DetectedLanguage


async def detect_language(state: ReplyState) -> dict[str, object]:
    """Detect Urdu script locally and ask the router only for Latin text."""
    if URDU_SCRIPT.search(state["text"]):
        return {"detected_language": "ur"}
    prompt = load_prompt("detect_language.md").format(
        reply=json.dumps({"text": state["text"]}, ensure_ascii=False)
    )
    result: LanguageOutput = await get_structured_llm(LanguageOutput).ainvoke(prompt)
    language = result.detected_language
    if language == "ur":
        language = "roman_ur"
    return {"detected_language": language}
