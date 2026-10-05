"""Deterministic English and Roman Urdu reply classification fallback."""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from app.models.enums import DeclineReason, ResponseIntent

URDU_RANGE = re.compile(r"[\u0600-\u06ff]")
CONFIRM_TERMS = ("confirm", "yes", "will come", "aaunga", "aunga", "aon ga", "haan", "han", "ji")
RESCHEDULE_TERMS = (
    "reschedule",
    "another time",
    "another day",
    "later",
    "tomorrow",
    "next week",
    "kal",
    "parson",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)
QUESTION_TERMS = ("where", "when", "which center", "address", "kahan", "kidhar", "kab")
TRAVELLING_TERMS = ("travelling", "traveling", "out of city", "shehar se bahar", "safar")
HEALTH_TERMS = ("health", "unwell", "sick", "tabiyat", "bemar", "bimaar")
RECENT_TERMS = ("recently donated", "month ago", "mahina pehle", "abhi diya", "already donated")
DECLINE_TERMS = ("decline", "not interested", "cannot come", "can't come", "nahi aa", "nahin aa")


@dataclass(frozen=True)
class FallbackResult:
    """Structured classification returned without an LLM."""

    intent: ResponseIntent
    confidence: float
    detected_language: str
    requested_date: date | None = None
    selected_slot_id: UUID | None = None
    decline_reason: DeclineReason | None = None


def classify_fallback(
    text: str,
    *,
    today: date,
    awaiting: str = "none",
    offered_slot_ids: tuple[UUID, ...] = (),
) -> FallbackResult:
    """Classify known demo phrases and return unknown for weak matches."""
    normalized = " ".join(text.casefold().split())
    language = _detected_language(text, normalized)
    if awaiting == "slot_choice":
        selected = _selected_slot(normalized, offered_slot_ids)
        if selected is not None:
            return FallbackResult(
                ResponseIntent.RESCHEDULE, 0.95, language, selected_slot_id=selected
            )
    if awaiting == "decline_reason":
        reason = _decline_reason(normalized) or DeclineReason.OTHER
        return FallbackResult(ResponseIntent.DECLINE, 0.9, language, decline_reason=reason)
    if any(term in normalized for term in RESCHEDULE_TERMS):
        return FallbackResult(
            ResponseIntent.RESCHEDULE,
            0.9,
            language,
            requested_date=_requested_date(normalized, today),
        )
    decline_reason = _decline_reason(normalized)
    if decline_reason is not None or any(term in normalized for term in DECLINE_TERMS):
        return FallbackResult(
            ResponseIntent.DECLINE,
            0.9,
            language,
            decline_reason=decline_reason,
        )
    if any(term in normalized for term in QUESTION_TERMS) or "?" in text:
        return FallbackResult(ResponseIntent.QUESTION, 0.85, language)
    if any(term in normalized for term in CONFIRM_TERMS):
        return FallbackResult(ResponseIntent.CONFIRM, 0.9, language)
    return FallbackResult(ResponseIntent.UNKNOWN, 0.0, language)


def _detected_language(text: str, normalized: str) -> str:
    if URDU_RANGE.search(text):
        return "ur"
    roman_terms = CONFIRM_TERMS[3:] + ("kal", "parson", "kahan", "kidhar", "tabiyat", "safar")
    return "roman_ur" if any(term in normalized for term in roman_terms) else "en"


def _decline_reason(text: str) -> DeclineReason | None:
    if any(term in text for term in TRAVELLING_TERMS):
        return DeclineReason.TRAVELLING
    if any(term in text for term in HEALTH_TERMS):
        return DeclineReason.HEALTH
    if any(term in text for term in RECENT_TERMS):
        return DeclineReason.RECENTLY_DONATED
    if "not interested" in text:
        return DeclineReason.NOT_INTERESTED
    return None


def _selected_slot(text: str, slot_ids: tuple[UUID, ...]) -> UUID | None:
    ordinals = (
        ("1", "first", "pehla"),
        ("2", "second", "doosra", "dusra"),
        ("3", "third", "teesra"),
    )
    for index, terms in enumerate(ordinals):
        if index < len(slot_ids) and any(term in text for term in terms):
            return slot_ids[index]
    return None


def _requested_date(text: str, today: date) -> date | None:
    if "tomorrow" in text or "kal" in text:
        return today + timedelta(days=1)
    if "next week" in text:
        return today + timedelta(days=7)
    return None
