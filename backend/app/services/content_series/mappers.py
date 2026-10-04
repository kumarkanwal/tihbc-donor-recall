"""Map content-series ORM aggregates to API schemas."""

from app.models.series import ContentSeries, SeriesStep
from app.repositories.content_series import ContentSeriesRecord
from app.schemas.content_series import (
    ContentSeriesDetail,
    ContentSeriesOut,
    QuickReplyButtonOut,
    SeriesStepContentOut,
    SeriesStepOut,
)
from app.schemas.donor_batch import UploadedBySummary


def series_out(record: ContentSeriesRecord) -> ContentSeriesOut:
    """Map a list record to its public summary."""
    return _series_base(record.series, record.step_count)


def series_detail(series: ContentSeries) -> ContentSeriesDetail:
    """Map a fully loaded series aggregate to detail output."""
    base = _series_base(series, len(series.steps))
    return ContentSeriesDetail(
        **base.model_dump(),
        steps=[step_out(step) for step in sorted(series.steps, key=lambda item: item.step_order)],
    )


def step_out(step: SeriesStep) -> SeriesStepOut:
    """Map one loaded step to API output."""
    contents = sorted(step.contents, key=lambda item: item.language.value)
    return SeriesStepOut(
        id=step.id,
        step_order=step.step_order,
        delay_days=step.delay_days,
        category=step.category,
        media_type=step.media_type,
        media_url=step.media_url,
        contents=[
            SeriesStepContentOut(id=item.id, language=item.language, body=item.body)
            for item in contents
        ],
        buttons=[QuickReplyButtonOut.model_validate(button) for button in step.buttons],
    )


def _series_base(series: ContentSeries, step_count: int) -> ContentSeriesOut:
    return ContentSeriesOut(
        id=series.id,
        name=series.name,
        description=series.description,
        kind=series.kind,
        status=series.status,
        languages=list(series.languages),
        response_window_hours=series.response_window_hours,
        tags=sorted(tag.name for tag in series.tags),
        step_count=step_count,
        created_by=UploadedBySummary(
            id=series.created_by.id,
            full_name=series.created_by.full_name,
        ),
        created_at=series.created_at,
        updated_at=series.updated_at,
    )
