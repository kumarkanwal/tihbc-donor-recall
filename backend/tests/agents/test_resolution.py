"""Deterministic multilingual date and offered-slot resolution."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.agents.resolution import resolve_offered_slot, resolve_requested_date
from app.agents.state import OfferedSlot

TODAY = date(2026, 10, 7)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Can I come Friday?", date(2026, 10, 9)),
        ("Kal nahi, Monday ko aa sakta hoon", date(2026, 10, 12)),
        ("aaj", TODAY),
        ("kal", date(2026, 10, 8)),
        ("Parson aa sakta hoon", date(2026, 10, 9)),
        ("tomorrow", date(2026, 10, 8)),
        ("next week", date(2026, 10, 14)),
        ("agli hafta", date(2026, 10, 14)),
        ("اگلے ہفتے آ سکتا ہوں", date(2026, 10, 14)),
        ("پرسوں آ سکتا ہوں", date(2026, 10, 9)),
        ("جمعہ", date(2026, 10, 9)),
    ],
)
def test_resolve_requested_date(text: str, expected: date) -> None:
    assert resolve_requested_date(text, TODAY) == expected


def test_resolve_slot_by_ordinal_and_weekday() -> None:
    slots = [
        _slot(datetime(2026, 10, 8, 10, tzinfo=UTC), "Thursday"),
        _slot(datetime(2026, 10, 10, 10, tzinfo=UTC), "Saturday"),
        _slot(datetime(2026, 10, 14, 10, tzinfo=UTC), "Wednesday"),
    ]

    assert resolve_offered_slot("first one", slots) == slots[0]
    assert resolve_offered_slot("2nd wala", slots) == slots[1]
    assert resolve_offered_slot("pehla", slots) == slots[0]
    assert resolve_offered_slot("Saturday wala", slots) == slots[1]


def _slot(starts_at: datetime, label: str) -> OfferedSlot:
    return OfferedSlot(
        id=uuid4(),
        starts_at=starts_at,
        center_name="Korangi Campus Blood Center",
        label=label,
    )
