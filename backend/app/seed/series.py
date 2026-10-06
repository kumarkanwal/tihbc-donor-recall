"""Persist the exact active demo content-series library."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from shutil import copyfile

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.enums import LanguageCode, MediaType, SeriesStatus
from app.models.series import ContentSeries, SeriesStep, SeriesStepContent, Tag
from app.models.user import User
from app.seed.content import RECALL_BUTTONS, SERIES_SEEDS, SeriesSeed, StepSeed

VIDEO_ASSET = Path(__file__).resolve().parent / "assets" / "donor-recall.mp4"
VIDEO_FILENAME = "donor-recall.mp4"


async def seed_content_series(
    session: AsyncSession,
    admin: User,
    settings: Settings,
    now: datetime,
) -> dict[str, ContentSeries]:
    """Persist all four active bilingual series and their reusable tags."""
    tag_names = sorted({tag for series in SERIES_SEEDS for tag in series.tags})
    tags = {name: Tag(name=name, created_at=now, updated_at=now) for name in tag_names}
    session.add_all(tags.values())
    media_url = _copy_video(settings)
    series_by_name = {
        seed.name: _build_series(seed, admin, tags, media_url, now) for seed in SERIES_SEEDS
    }
    session.add_all(series_by_name.values())
    await session.flush()
    return series_by_name


def _build_series(
    seed: SeriesSeed,
    admin: User,
    tags: dict[str, Tag],
    media_url: str | None,
    now: datetime,
) -> ContentSeries:
    series = ContentSeries(
        name=seed.name,
        description=seed.description,
        kind=seed.kind,
        status=SeriesStatus.ACTIVE,
        languages=[LanguageCode.EN, LanguageCode.UR],
        response_window_hours=48,
        created_by=admin,
        tags=[tags[name] for name in seed.tags],
        created_at=now,
        updated_at=now,
    )
    series.steps = [
        _build_step(series, order, step, media_url, now)
        for order, step in enumerate(seed.steps, start=1)
    ]
    return series


def _build_step(
    series: ContentSeries,
    order: int,
    seed: StepSeed,
    media_url: str | None,
    now: datetime,
) -> SeriesStep:
    has_video = seed.video and media_url is not None
    step = SeriesStep(
        series=series,
        step_order=order,
        delay_days=seed.delay_days,
        category=seed.category,
        media_type=MediaType.VIDEO if has_video else MediaType.NONE,
        media_url=media_url if has_video else None,
        buttons=deepcopy(RECALL_BUTTONS),
        created_at=now,
        updated_at=now,
    )
    step.contents = [
        SeriesStepContent(
            step=step,
            language=language,
            body=body,
            created_at=now,
            updated_at=now,
        )
        for language, body in (
            (LanguageCode.EN, seed.english),
            (LanguageCode.UR, seed.urdu),
        )
    ]
    return step


def _copy_video(settings: Settings) -> str | None:
    if not VIDEO_ASSET.is_file():
        return None
    destination_directory = settings.media_storage_dir
    destination_directory.mkdir(parents=True, exist_ok=True)
    copyfile(VIDEO_ASSET, destination_directory / VIDEO_FILENAME)
    return f"{settings.media_public_url.rstrip('/')}/{VIDEO_FILENAME}"
