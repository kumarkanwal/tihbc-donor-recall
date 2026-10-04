"""Tests for aggregate campaign launch validation."""

from uuid import uuid4

from app.core.clock import clock
from app.models.campaign import Campaign
from app.models.enums import (
    CampaignStatus,
    LanguageCode,
    SeriesKind,
    SeriesStatus,
)
from app.models.series import ContentSeries
from app.schemas.campaign import CampaignLaunchProblem
from app.services.campaigns.validation import launch_problems


def test_launch_validation_returns_every_problem_at_once() -> None:
    campaign = _campaign(
        primary=_series(SeriesKind.SECONDARY, SeriesStatus.DRAFT, [LanguageCode.EN]),
        secondary=_series(SeriesKind.PRIMARY, SeriesStatus.ARCHIVED, [LanguageCode.EN]),
    )

    problems = launch_problems(
        campaign,
        ((LanguageCode.UR, 1),),
        batch_has_live_campaign=True,
    )

    assert {(problem.field, problem.reason) for problem in problems} == {
        ("primary_series_id", "Series kind must be primary"),
        ("primary_series_id", "Series must be active"),
        ("primary_series_id", "Series is missing donor languages: ur"),
        ("secondary_series_id", "Series kind must be secondary"),
        ("secondary_series_id", "Series must be active"),
        ("secondary_series_id", "Series is missing donor languages: ur"),
        (
            "batch_id",
            "Batch is already used by a scheduled, running, or paused campaign",
        ),
    }


def test_empty_batch_is_reported() -> None:
    campaign = _campaign(
        primary=_series(SeriesKind.PRIMARY, SeriesStatus.ACTIVE, [LanguageCode.EN]),
        secondary=_series(SeriesKind.SECONDARY, SeriesStatus.ACTIVE, [LanguageCode.EN]),
    )

    problems = launch_problems(campaign, (), batch_has_live_campaign=False)

    assert problems == [
        CampaignLaunchProblem(field="batch_id", reason="Batch must contain at least one donor")
    ]


def test_valid_campaign_has_no_launch_problems() -> None:
    campaign = _campaign(
        primary=_series(
            SeriesKind.PRIMARY,
            SeriesStatus.ACTIVE,
            [LanguageCode.EN, LanguageCode.UR],
        ),
        secondary=_series(
            SeriesKind.SECONDARY,
            SeriesStatus.ACTIVE,
            [LanguageCode.EN, LanguageCode.UR],
        ),
    )

    problems = launch_problems(
        campaign,
        ((LanguageCode.EN, 2), (LanguageCode.UR, 1)),
        batch_has_live_campaign=False,
    )

    assert problems == []


def _campaign(*, primary: ContentSeries, secondary: ContentSeries) -> Campaign:
    campaign = Campaign(
        name="Validation Test",
        batch_id=uuid4(),
        primary_series_id=primary.id,
        secondary_series_id=secondary.id,
        status=CampaignStatus.DRAFT,
        start_at=clock.now(),
        created_by_id=uuid4(),
    )
    campaign.primary_series = primary
    campaign.secondary_series = secondary
    return campaign


def _series(
    kind: SeriesKind,
    status: SeriesStatus,
    languages: list[LanguageCode],
) -> ContentSeries:
    return ContentSeries(
        name=f"{kind.value} series",
        kind=kind,
        status=status,
        languages=languages,
        created_by_id=uuid4(),
    )
