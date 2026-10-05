"""Keyword fallback classification in English and Roman Urdu."""

from datetime import date

import pytest

from app.agents.fallback import classify_fallback
from app.models.enums import DeclineReason, ResponseIntent

TODAY = date(2026, 10, 5)


@pytest.mark.parametrize(
    ("text", "intent", "reason"),
    [
        ("Yes I will come", ResponseIntent.CONFIRM, None),
        ("Ji main aaunga", ResponseIntent.CONFIRM, None),
        ("Kal nahi, Monday ko aa sakta hoon", ResponseIntent.RESCHEDULE, None),
        ("Main shehar se bahar hoon", ResponseIntent.DECLINE, DeclineReason.TRAVELLING),
        ("Tabiyat theek nahi", ResponseIntent.DECLINE, DeclineReason.HEALTH),
        ("Abhi 1 mahina pehle diya tha", ResponseIntent.DECLINE, DeclineReason.RECENTLY_DONATED),
        ("Where is the center?", ResponseIntent.QUESTION, None),
        ("asdfgh", ResponseIntent.UNKNOWN, None),
    ],
)
def test_fallback_examples(text: str, intent: ResponseIntent, reason: DeclineReason | None) -> None:
    result = classify_fallback(text, today=TODAY)

    assert result.intent == intent
    assert result.decline_reason == reason


def test_fallback_resolves_ordinal_against_offered_slots() -> None:
    from uuid import uuid4

    slots = (uuid4(), uuid4(), uuid4())

    result = classify_fallback(
        "2nd wala", today=TODAY, awaiting="slot_choice", offered_slot_ids=slots
    )

    assert result.intent == ResponseIntent.RESCHEDULE
    assert result.selected_slot_id == slots[1]
