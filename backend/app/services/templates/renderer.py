"""Render approved message variables and localized quick replies."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.errors import ValidationError
from app.models.enums import LanguageCode

VARIABLE_PATTERN = re.compile(r"{{\s*([^{}]+?)\s*}}")
ALLOWED_VARIABLES = frozenset({"donor_name", "center_name", "appointment_date"})
ENGLISH_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
ENGLISH_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
URDU_WEEKDAYS = ("پیر", "منگل", "بدھ", "جمعرات", "جمعہ", "ہفتہ", "اتوار")
URDU_MONTHS = (
    "جنوری",
    "فروری",
    "مارچ",
    "اپریل",
    "مئی",
    "جون",
    "جولائی",
    "اگست",
    "ستمبر",
    "اکتوبر",
    "نومبر",
    "دسمبر",
)
URDU_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
APPOINTMENT_FALLBACKS = {
    LanguageCode.EN: "at your earliest convenience",
    LanguageCode.UR: "اپنی جلد از جلد سہولت کے مطابق",
}


@dataclass(frozen=True)
class TemplateValues:
    """Values available to every message template."""

    donor_name: str
    center_name: str
    appointment_date: datetime | None


@dataclass(frozen=True)
class ButtonTemplate:
    """Language-keyed quick-reply definition."""

    id: str
    intent: str
    labels: Mapping[LanguageCode, str]


@dataclass(frozen=True)
class LocalizedButton:
    """Quick reply rendered for one donor language."""

    id: str
    intent: str
    label: str


def validate_template(body: str) -> None:
    """Reject variables outside the approved template vocabulary."""
    variables = {match.group(1).strip() for match in VARIABLE_PATTERN.finditer(body)}
    unknown = sorted(variables - ALLOWED_VARIABLES)
    if unknown:
        raise ValidationError(
            "Message body contains unknown variables",
            {"variables": unknown},
        )


def render_body(
    body: str,
    language: LanguageCode,
    values: TemplateValues,
    timezone_display: str,
) -> str:
    """Render one localized message body in the configured display timezone."""
    validate_template(body)
    replacements = {
        "donor_name": values.donor_name,
        "center_name": values.center_name,
        "appointment_date": format_appointment_date(
            values.appointment_date, language, timezone_display
        ),
    }
    return VARIABLE_PATTERN.sub(
        lambda match: replacements[match.group(1).strip()],
        body,
    )


def localize_buttons(
    buttons: Sequence[ButtonTemplate], language: LanguageCode
) -> list[LocalizedButton]:
    """Select one localized label for every quick reply."""
    localized: list[LocalizedButton] = []
    for button in buttons:
        label = button.labels.get(language)
        if label is None:
            raise ValidationError(
                "Button label is missing for language",
                {"button_id": button.id, "language": language.value},
            )
        localized.append(LocalizedButton(id=button.id, intent=button.intent, label=label))
    return localized


def format_appointment_date(
    value: datetime | None,
    language: LanguageCode,
    timezone_display: str,
) -> str:
    """Format an appointment using the documented bilingual slot style."""
    if value is None:
        return APPOINTMENT_FALLBACKS[language]
    if value.tzinfo is None:
        raise ValidationError("Appointment date must include a timezone")
    try:
        local_value = value.astimezone(ZoneInfo(timezone_display))
    except ZoneInfoNotFoundError as error:
        raise ValidationError("Invalid display timezone") from error
    if language == LanguageCode.UR:
        return _format_urdu(local_value)
    return _format_english(local_value)


def _format_english(value: datetime) -> str:
    hour = value.hour % 12 or 12
    minute = f":{value.minute:02d}" if value.minute else ":00"
    period = "AM" if value.hour < 12 else "PM"
    return (
        f"{ENGLISH_WEEKDAYS[value.weekday()]} {value.day} "
        f"{ENGLISH_MONTHS[value.month - 1]}, {hour}{minute} {period}"
    )


def _format_urdu(value: datetime) -> str:
    hour = value.hour % 12 or 12
    time_text = str(hour) if value.minute == 0 else f"{hour}:{value.minute:02d}"
    period = "صبح" if value.hour < 12 else "شام"
    rendered = (
        f"{URDU_WEEKDAYS[value.weekday()]} {value.day} "
        f"{URDU_MONTHS[value.month - 1]}، {period} {time_text} بجے"
    )
    return rendered.translate(URDU_DIGITS)
