"""Render approved automatic replies and dynamic quick-reply buttons."""

from app.models.campaign import AppointmentSlot, Enrollment
from app.models.enums import LanguageCode
from app.services.appointments.centers import center_for_city
from app.services.replies.en import TEMPLATES as ENGLISH_TEMPLATES
from app.services.replies.ur import TEMPLATES as URDU_TEMPLATES
from app.services.templates.renderer import TemplateValues, format_appointment_date, render_body

DECLINE_BUTTONS = {
    LanguageCode.EN: (
        ("btn_reason_travelling", "Travelling"),
        ("btn_reason_health", "Health reason"),
        ("btn_reason_other", "Other"),
    ),
    LanguageCode.UR: (
        ("btn_reason_travelling", "سفر میں ہوں"),
        ("btn_reason_health", "صحت کی وجہ"),
        ("btn_reason_other", "کوئی اور وجہ"),
    ),
}


def render_reply(
    key: str,
    enrollment: Enrollment,
    appointment: AppointmentSlot | None,
    timezone_display: str,
) -> str:
    """Render one exact demo-content automatic reply."""
    language = enrollment.donor.language
    templates = URDU_TEMPLATES if language == LanguageCode.UR else ENGLISH_TEMPLATES
    return render_body(
        templates[key],
        language,
        TemplateValues(
            donor_name=enrollment.donor.full_name,
            center_name=(
                appointment.center_name
                if appointment is not None
                else center_for_city(enrollment.donor.city)
            ),
            appointment_date=appointment.starts_at if appointment is not None else None,
        ),
        timezone_display,
    )


def decline_buttons(language: LanguageCode) -> list[dict[str, object]]:
    """Return localized decline-reason buttons with internal intent metadata."""
    return [
        {"id": button_id, "intent": "decline", "label": label}
        for button_id, label in DECLINE_BUTTONS[language]
    ]


def slot_buttons(
    slots: tuple[AppointmentSlot, ...], language: LanguageCode, timezone_display: str
) -> list[dict[str, object]]:
    """Return localized appointment buttons carrying stable slot identifiers."""
    return [
        {
            "id": f"slot_{slot.id.hex}",
            "intent": "reschedule",
            "label": format_appointment_date(slot.starts_at, language, timezone_display),
        }
        for slot in slots
    ]
