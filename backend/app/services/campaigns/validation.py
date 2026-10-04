"""Campaign launch validation."""

from app.models.campaign import Campaign
from app.models.enums import LanguageCode, SeriesKind, SeriesStatus
from app.schemas.campaign import CampaignLaunchProblem


def launch_problems(
    campaign: Campaign,
    donor_language_counts: tuple[tuple[LanguageCode, int], ...],
    *,
    batch_has_live_campaign: bool,
) -> list[CampaignLaunchProblem]:
    """Return every launch problem without short-circuiting."""
    problems: list[CampaignLaunchProblem] = []
    donor_languages = {language for language, _count in donor_language_counts}
    donor_count = sum(count for _language, count in donor_language_counts)
    problems.extend(
        _series_problems(
            "primary_series_id",
            campaign.primary_series.kind,
            SeriesKind.PRIMARY,
            campaign.primary_series.status,
            set(campaign.primary_series.languages),
            donor_languages,
        )
    )
    problems.extend(
        _series_problems(
            "secondary_series_id",
            campaign.secondary_series.kind,
            SeriesKind.SECONDARY,
            campaign.secondary_series.status,
            set(campaign.secondary_series.languages),
            donor_languages,
        )
    )
    if donor_count == 0:
        problems.append(
            CampaignLaunchProblem(field="batch_id", reason="Batch must contain at least one donor")
        )
    if batch_has_live_campaign:
        problems.append(
            CampaignLaunchProblem(
                field="batch_id",
                reason="Batch is already used by a scheduled, running, or paused campaign",
            )
        )
    return problems


def _series_problems(
    field: str,
    actual_kind: SeriesKind,
    required_kind: SeriesKind,
    status: SeriesStatus,
    series_languages: set[LanguageCode],
    donor_languages: set[LanguageCode],
) -> list[CampaignLaunchProblem]:
    problems: list[CampaignLaunchProblem] = []
    if actual_kind != required_kind:
        problems.append(
            CampaignLaunchProblem(
                field=field,
                reason=f"Series kind must be {required_kind.value}",
            )
        )
    if status != SeriesStatus.ACTIVE:
        problems.append(CampaignLaunchProblem(field=field, reason="Series must be active"))
    missing = sorted(language.value for language in donor_languages - series_languages)
    if missing:
        problems.append(
            CampaignLaunchProblem(
                field=field,
                reason=f"Series is missing donor languages: {', '.join(missing)}",
            )
        )
    return problems
