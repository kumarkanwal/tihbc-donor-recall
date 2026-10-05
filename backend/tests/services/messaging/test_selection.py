"""Tests for primary and secondary series step selection."""

from uuid import uuid4

from app.core.clock import clock
from app.models.campaign import Campaign, Enrollment
from app.models.enums import CampaignStatus, EnrollmentStatus, SeriesKind, SeriesStatus
from app.models.series import ContentSeries, SeriesStep
from app.services.messaging.selection import select_next_step


def test_selection_stays_with_current_series_until_escalation_switches_it() -> None:
    primary = _series(SeriesKind.PRIMARY, (1, 2))
    secondary = _series(SeriesKind.SECONDARY, (1,))
    enrollment = _enrollment(primary, secondary)
    enrollment.current_step_order = 1

    primary_selection = select_next_step(enrollment)
    assert primary_selection is not None
    assert primary_selection.series is primary
    assert primary_selection.step.step_order == 2

    enrollment.current_series_kind = SeriesKind.SECONDARY
    enrollment.current_step_order = None
    secondary_selection = select_next_step(enrollment)
    assert secondary_selection is not None
    assert secondary_selection.series is secondary
    assert secondary_selection.step.step_order == 1


def _series(kind: SeriesKind, orders: tuple[int, ...]) -> ContentSeries:
    series = ContentSeries(
        name=kind.value,
        kind=kind,
        status=SeriesStatus.ACTIVE,
        languages=[],
        created_by_id=uuid4(),
    )
    series.steps = [SeriesStep(step_order=order, delay_days=order) for order in orders]
    return series


def _enrollment(primary: ContentSeries, secondary: ContentSeries) -> Enrollment:
    campaign = Campaign(
        name="Campaign",
        batch_id=uuid4(),
        primary_series_id=uuid4(),
        secondary_series_id=uuid4(),
        status=CampaignStatus.RUNNING,
        start_at=clock.now(),
        created_by_id=uuid4(),
    )
    campaign.primary_series = primary
    campaign.secondary_series = secondary
    return Enrollment(
        campaign=campaign,
        donor_id=uuid4(),
        status=EnrollmentStatus.IN_PRIMARY,
        current_series_kind=SeriesKind.PRIMARY,
        current_step_order=None,
        next_action_at=clock.now(),
    )
