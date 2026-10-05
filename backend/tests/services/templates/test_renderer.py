"""Tests for bilingual message-template rendering."""

from datetime import UTC, datetime

import pytest

from app.core.errors import ValidationError
from app.models.enums import LanguageCode
from app.services.templates.renderer import (
    ButtonTemplate,
    TemplateValues,
    format_appointment_date,
    localize_buttons,
    render_body,
    validate_template,
)

APPOINTMENT = datetime(2026, 10, 3, 5, tzinfo=UTC)
VALUES = TemplateValues(
    donor_name="Ahmed Raza",
    center_name="Korangi Campus Blood Center",
    appointment_date=APPOINTMENT,
)


def test_render_body_replaces_every_approved_variable() -> None:
    rendered = render_body(
        "{{donor_name}} at {{center_name}} on {{appointment_date}}",
        LanguageCode.EN,
        VALUES,
        "Asia/Karachi",
    )

    assert rendered == ("Ahmed Raza at Korangi Campus Blood Center on Sat 3 Oct, 10:00 AM")


def test_appointment_date_has_english_and_urdu_formats() -> None:
    assert (
        format_appointment_date(APPOINTMENT, LanguageCode.EN, "Asia/Karachi")
        == "Sat 3 Oct, 10:00 AM"
    )
    assert (
        format_appointment_date(APPOINTMENT, LanguageCode.UR, "Asia/Karachi")
        == "ہفتہ ۳ اکتوبر، صبح ۱۰ بجے"
    )


def test_missing_appointment_uses_localized_fallback() -> None:
    assert (
        format_appointment_date(None, LanguageCode.EN, "Asia/Karachi")
        == "at your earliest convenience"
    )
    assert (
        format_appointment_date(None, LanguageCode.UR, "Asia/Karachi")
        == "اپنی جلد از جلد سہولت کے مطابق"
    )


def test_buttons_are_localized_for_requested_language() -> None:
    buttons = [
        ButtonTemplate(
            id="btn_confirm",
            intent="confirm",
            labels={LanguageCode.EN: "Confirm", LanguageCode.UR: "تصدیق کریں"},
        )
    ]

    assert localize_buttons(buttons, LanguageCode.UR)[0].label == "تصدیق کریں"


def test_unknown_template_variable_is_rejected() -> None:
    with pytest.raises(ValidationError) as error:
        validate_template("Hello {{donor_phone}}")

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.details == {"variables": ["donor_phone"]}


def test_naive_appointment_date_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        format_appointment_date(
            datetime(2026, 10, 3, 10),
            LanguageCode.EN,
            "Asia/Karachi",
        )
