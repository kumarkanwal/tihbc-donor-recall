"""Render one selected series step for its enrolled donor."""

from dataclasses import dataclass

from app.models.campaign import AppointmentSlot, Enrollment
from app.schemas.content_series import QuickReplyButtonInput
from app.services.messaging.selection import SelectedStep
from app.services.templates.renderer import (
    ButtonTemplate,
    TemplateValues,
    localize_buttons,
    render_body,
)


@dataclass(frozen=True)
class RenderedStep:
    """Localized body and JSON-ready quick replies."""

    body: str
    buttons: tuple[dict[str, str], ...]


def render_step(
    enrollment: Enrollment,
    selection: SelectedStep,
    appointment: AppointmentSlot,
    timezone_display: str,
) -> RenderedStep:
    """Render the donor-language content and quick-reply labels."""
    language = enrollment.donor.language
    content = next(item for item in selection.step.contents if item.language == language)
    button_inputs = [QuickReplyButtonInput.model_validate(item) for item in selection.step.buttons]
    localized = localize_buttons(
        [
            ButtonTemplate(id=item.id, intent=item.intent, labels=item.labels)
            for item in button_inputs
        ],
        language,
    )
    values = TemplateValues(
        donor_name=enrollment.donor.full_name,
        center_name=appointment.center_name,
        appointment_date=appointment.starts_at,
    )
    return RenderedStep(
        body=render_body(content.body, language, values, timezone_display),
        buttons=tuple(
            {"id": button.id, "intent": button.intent, "label": button.label}
            for button in localized
        ),
    )
