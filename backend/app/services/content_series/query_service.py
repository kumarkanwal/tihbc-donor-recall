"""Read and preview content-series aggregates."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.enums import (
    LanguageCode,
    MessageDirection,
    MessageKind,
    MessageStatus,
    SeriesKind,
    SeriesStatus,
)
from app.models.series import ContentSeries
from app.repositories.content_series import ContentSeriesRepository
from app.repositories.donor import DonorRepository
from app.schemas.content_series import (
    ContentSeriesDetail,
    ContentSeriesPage,
    PreviewButtonOut,
    QuickReplyButtonOut,
    SeriesPreviewInput,
    SeriesPreviewMessage,
)
from app.services.content_series.mappers import series_detail, series_out
from app.services.templates.renderer import (
    ButtonTemplate,
    TemplateValues,
    localize_buttons,
    render_body,
)

SAMPLE_DONOR_NAME = "Ahmed Raza"
SAMPLE_CENTER_NAME = "Korangi Campus Blood Center"


class ContentSeriesQueryService:
    """Return API-safe content-series reads and rendered previews."""

    def __init__(
        self,
        series_repository: ContentSeriesRepository,
        donor_repository: DonorRepository,
        current_clock: Clock,
        timezone_display: str,
    ) -> None:
        self._series = series_repository
        self._donors = donor_repository
        self._clock = current_clock
        self._timezone_display = timezone_display

    async def list_series(
        self,
        *,
        kind: SeriesKind | None,
        status: SeriesStatus | None,
        tag: str | None,
        language: LanguageCode | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> ContentSeriesPage:
        """Return a filtered page of content-series summaries."""
        result = await self._series.list_filtered(
            kind=kind,
            status=status,
            tag=tag,
            language=language,
            search=search,
            page=page,
            page_size=page_size,
        )
        return ContentSeriesPage(
            items=[series_out(item) for item in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def get_series(self, series_id: UUID) -> ContentSeriesDetail:
        """Return one complete content series."""
        return series_detail(await self._required_series(series_id))

    async def preview(self, series_id: UUID, request: SeriesPreviewInput) -> SeriesPreviewMessage:
        """Render one step with a real donor or documented sample values."""
        series = await self._required_series(series_id)
        if request.language not in series.languages:
            raise ValidationError("Preview language is not enabled for the series")
        step = next((item for item in series.steps if item.id == request.step_id), None)
        if step is None:
            raise NotFoundError("Series step not found")
        content = next((item for item in step.contents if item.language == request.language), None)
        if content is None or not content.body.strip():
            raise ValidationError("Step content is missing for the preview language")
        donor_name = await self._donor_name(request.donor_id)
        values = TemplateValues(
            donor_name=donor_name,
            center_name=SAMPLE_CENTER_NAME,
            appointment_date=self._sample_appointment(),
        )
        buttons = [QuickReplyButtonOut.model_validate(item) for item in step.buttons]
        localized = localize_buttons(
            [
                ButtonTemplate(id=item.id, intent=item.intent, labels=item.labels)
                for item in buttons
            ],
            request.language,
        )
        return SeriesPreviewMessage(
            id=uuid4(),
            donor_id=request.donor_id,
            direction=MessageDirection.OUTBOUND,
            kind=MessageKind.TEMPLATE,
            body=render_body(content.body, request.language, values, self._timezone_display),
            media_type=step.media_type,
            media_url=step.media_url,
            buttons=[PreviewButtonOut(id=item.id, label=item.label) for item in localized],
            status=MessageStatus.QUEUED,
            created_at=self._clock.now(),
        )

    async def _required_series(self, series_id: UUID) -> ContentSeries:
        series = await self._series.get_full(series_id)
        if series is None:
            raise NotFoundError("Content series not found")
        return series

    async def _donor_name(self, donor_id: UUID | None) -> str:
        if donor_id is None:
            return SAMPLE_DONOR_NAME
        donor = await self._donors.get(donor_id)
        if donor is None:
            raise NotFoundError("Donor not found")
        return donor.full_name

    def _sample_appointment(self) -> datetime:
        local_now = self._clock.now().astimezone(ZoneInfo(self._timezone_display))
        local_appointment = (local_now + timedelta(days=2)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        return local_appointment.astimezone(UTC)
