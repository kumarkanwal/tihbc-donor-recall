"""Select the next ordered step for an enrollment's current series."""

from dataclasses import dataclass

from app.models.campaign import Enrollment
from app.models.enums import SeriesKind
from app.models.series import ContentSeries, SeriesStep


@dataclass(frozen=True)
class SelectedStep:
    """The current series and its next unsent step."""

    series: ContentSeries
    step: SeriesStep
    following_step: SeriesStep | None


def select_next_step(enrollment: Enrollment) -> SelectedStep | None:
    """Return the next ordered step without crossing an escalation boundary."""
    series = _current_series(enrollment)
    current_order = enrollment.current_step_order or 0
    remaining = [step for step in series.steps if step.step_order > current_order]
    if not remaining:
        return None
    ordered = sorted(remaining, key=lambda step: step.step_order)
    following = ordered[1] if len(ordered) > 1 else None
    return SelectedStep(series=series, step=ordered[0], following_step=following)


def _current_series(enrollment: Enrollment) -> ContentSeries:
    if enrollment.current_series_kind == SeriesKind.SECONDARY:
        return enrollment.campaign.secondary_series
    return enrollment.campaign.primary_series
