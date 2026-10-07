"""Deterministic reschedule-date and offered-slot resolution."""

from datetime import date, timedelta

from app.agents.state import OfferedSlot

_PUNCTUATION = str.maketrans({character: " " for character in ",.!?;:()[]{}\"'`،؟۔/\\-_"})

_WEEKDAY_ALIASES: tuple[tuple[str, ...], ...] = (
    ("monday", "somwar", "sombar", "pir", "peer", "پیر"),
    ("tuesday", "mangal", "منگل"),
    ("wednesday", "budh", "budhwar", "بدھ"),
    ("thursday", "jumerat", "jumeraat", "جمعرات"),
    ("friday", "jumma", "jumuah", "جمعہ"),
    ("saturday", "hafta", "sanichar", "ہفتہ"),
    ("sunday", "itwar", "اتوار"),
)
_NEXT_WEEK = (
    "next week",
    "aglay haftay",
    "agley haftay",
    "agle haftay",
    "agli hafta",
    "اگلے ہفتے",
)
_DAY_AFTER_TOMORROW = ("day after tomorrow", "parson", "parso", "پرسوں")
_TOMORROW = ("tomorrow", "kal", "کل")
_TODAY = ("today", "aaj", "آج")
_ORDINAL_ALIASES: tuple[tuple[str, ...], ...] = (
    ("1", "1st", "first", "first one", "pehla", "pehli", "پہلا", "پہلی"),
    ("2", "2nd", "second", "second one", "doosra", "dusra", "دوسرا"),
    ("3", "3rd", "third", "third one", "teesra", "تیسرا"),
)
_ROMAN_URDU_MARKERS = (
    "aa sakta",
    "aaj",
    "aglay",
    "agley",
    "doosra",
    "dusra",
    "haftay",
    "kal",
    "parson",
    "pehla",
    "pehli",
    "teesra",
    "wala",
)


def normalize_reply(text: str) -> str:
    """Normalize spacing and punctuation while preserving Urdu characters."""
    return " ".join(text.casefold().translate(_PUNCTUATION).split())


def resolve_requested_date(text: str, today: date) -> date | None:
    """Resolve supported future date expressions against the supplied demo date."""
    normalized = normalize_reply(text)
    if _contains_any(normalized, _NEXT_WEEK):
        return today + timedelta(days=7)
    weekday = _weekday_from_text(normalized)
    if weekday is not None:
        return _next_weekday(today, weekday)
    if _contains_any(normalized, _DAY_AFTER_TOMORROW):
        return today + timedelta(days=2)
    if _contains_any(normalized, _TOMORROW):
        return today + timedelta(days=1)
    if _contains_any(normalized, _TODAY):
        return today
    return None


def resolve_offered_slot(text: str, offered_slots: list[OfferedSlot]) -> OfferedSlot | None:
    """Map ordinal or weekday wording to one of the slots actually offered."""
    normalized = normalize_reply(text)
    for index, aliases in enumerate(_ORDINAL_ALIASES):
        if index < len(offered_slots) and _contains_any(normalized, aliases):
            return offered_slots[index]
    weekday = _weekday_from_text(normalized)
    if weekday is None:
        return None
    return next(
        (slot for slot in offered_slots if slot.starts_at.date().weekday() == weekday),
        None,
    )


def is_ambiguous_reply(text: str) -> bool:
    """Identify deliberately non-committal evaluation replies."""
    return normalize_reply(text) in {"", "maybe", "shayad", "شاید"}


def looks_roman_urdu(text: str) -> bool:
    """Return whether deterministic reply wording is recognizably Roman Urdu."""
    normalized = normalize_reply(text)
    return _contains_any(normalized, _ROMAN_URDU_MARKERS)


def _weekday_from_text(normalized: str) -> int | None:
    for weekday, aliases in enumerate(_WEEKDAY_ALIASES):
        if _contains_any(normalized, aliases):
            return weekday
    return None


def _contains_any(normalized: str, phrases: tuple[str, ...]) -> bool:
    padded = f" {normalized} "
    return any(f" {phrase} " in padded for phrase in phrases)


def _next_weekday(today: date, weekday: int) -> date:
    days = (weekday - today.weekday()) % 7
    return today + timedelta(days=days or 7)
