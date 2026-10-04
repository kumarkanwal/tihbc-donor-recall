"""Content-series draft and activation validation."""

from collections.abc import Sequence

from app.core.errors import ValidationError
from app.models.enums import LanguageCode, MediaType
from app.models.series import ContentSeries, SeriesStep
from app.schemas.content_series import (
    ActivationProblem,
    QuickReplyButtonInput,
    SeriesStepContentInput,
)
from app.services.templates.renderer import validate_template


def validate_step_values(
    series_languages: Sequence[LanguageCode],
    contents: Sequence[SeriesStepContentInput],
    buttons: Sequence[QuickReplyButtonInput],
) -> None:
    """Validate relationships between a step payload and its series."""
    supported = set(series_languages)
    unsupported = sorted(
        {content.language for content in contents if content.language not in supported},
        key=lambda item: item.value,
    )
    if unsupported:
        raise ValidationError(
            "Step content language is not enabled for the series",
            {"languages": [language.value for language in unsupported]},
        )
    for content in contents:
        validate_template(content.body)
    for button in buttons:
        missing = [language.value for language in series_languages if language not in button.labels]
        if missing:
            raise ValidationError(
                "Button label is missing for a series language",
                {"button_id": button.id, "languages": missing},
            )


def activation_problems(series: ContentSeries) -> list[ActivationProblem]:
    """Return every problem preventing activation of one loaded series."""
    if not series.steps:
        return [
            ActivationProblem(
                step=None,
                language=None,
                field="steps",
                reason="At least one step is required",
            )
        ]
    problems: list[ActivationProblem] = []
    for step in sorted(series.steps, key=lambda item: item.step_order):
        problems.extend(_step_problems(step, series.languages))
    return problems


def _step_problems(step: SeriesStep, languages: Sequence[LanguageCode]) -> list[ActivationProblem]:
    problems: list[ActivationProblem] = []
    contents = {content.language: content.body for content in step.contents}
    for language in languages:
        body = contents.get(language, "")
        if not body.strip():
            problems.append(
                ActivationProblem(
                    step=step.step_order,
                    language=language,
                    field="body",
                    reason="Content is required for the series language",
                )
            )
    if step.media_type != MediaType.NONE and not step.media_url:
        problems.append(
            ActivationProblem(
                step=step.step_order,
                language=None,
                field="media_url",
                reason="Media URL is required when media type is not none",
            )
        )
    return problems
