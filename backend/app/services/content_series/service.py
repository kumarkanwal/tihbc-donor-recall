"""Content-series lifecycle business logic."""

from copy import deepcopy
from uuid import UUID

from app.core.errors import ConflictError, ValidationError
from app.models.enums import LanguageCode, SeriesStatus
from app.models.series import ContentSeries, SeriesStep, SeriesStepContent
from app.schemas.content_series import (
    ContentSeriesCreate,
    ContentSeriesDetail,
    ContentSeriesUpdate,
    QuickReplyButtonInput,
)
from app.schemas.user import UserOut
from app.services.content_series.access import ContentSeriesAccess
from app.services.content_series.mappers import series_detail
from app.services.content_series.validation import activation_problems, validate_step_values


class ContentSeriesService:
    """Create, update, activate, archive, and duplicate content series."""

    def __init__(self, access: ContentSeriesAccess) -> None:
        self._access = access

    async def create(
        self, request: ContentSeriesCreate, created_by: UserOut
    ) -> ContentSeriesDetail:
        """Create a draft series and normalized tags."""
        tags = await self._access.repository.get_or_create_tags(request.tag_names)
        series = ContentSeries(
            name=request.name,
            description=request.description or None,
            kind=request.kind,
            status=SeriesStatus.DRAFT,
            languages=list(request.languages),
            response_window_hours=request.response_window_hours,
            created_by_id=created_by.id,
            tags=tags,
        )
        await self._access.repository.add(series)
        await self._access.commit()
        return series_detail(await self._access.reload(series.id))

    async def update(self, series_id: UUID, request: ContentSeriesUpdate) -> ContentSeriesDetail:
        """Update editable series settings."""
        series = await self._access.editable(series_id)
        fields = request.model_fields_set
        if "name" in fields and request.name is not None:
            series.name = request.name
        if "description" in fields:
            series.description = request.description or None
        if request.kind is not None:
            series.kind = request.kind
        if request.languages is not None:
            self._validate_existing_buttons(series, request.languages)
            series.languages = list(request.languages)
        if request.response_window_hours is not None:
            series.response_window_hours = request.response_window_hours
        if request.tag_names is not None:
            series.tags = await self._access.repository.get_or_create_tags(request.tag_names)
        self._access.ensure_active_valid(series)
        await self._access.commit()
        return series_detail(await self._access.reload(series.id))

    async def activate(self, series_id: UUID) -> ContentSeriesDetail:
        """Activate a complete, non-archived series."""
        series = await self._access.required(series_id)
        if series.status == SeriesStatus.ARCHIVED:
            raise ConflictError("Archived content series cannot be activated")
        problems = activation_problems(series)
        if problems:
            raise ValidationError(
                "Content series cannot be activated",
                {"problems": [problem.model_dump(mode="json") for problem in problems]},
            )
        series.status = SeriesStatus.ACTIVE
        await self._access.commit()
        return series_detail(await self._access.reload(series.id))

    async def archive(self, series_id: UUID) -> ContentSeriesDetail:
        """Archive a series that is not attached to a live campaign."""
        series = await self._access.required(series_id)
        if await self._access.repository.has_edit_blocking_campaign(series_id):
            raise ConflictError("Content series is used by an active campaign")
        series.status = SeriesStatus.ARCHIVED
        await self._access.commit()
        return series_detail(await self._access.reload(series.id))

    async def duplicate(self, series_id: UUID, created_by: UserOut) -> ContentSeriesDetail:
        """Deep-copy a series as a new draft."""
        source = await self._access.required(series_id)
        duplicate = ContentSeries(
            name=f"{source.name} (copy)",
            description=source.description,
            kind=source.kind,
            status=SeriesStatus.DRAFT,
            languages=list(source.languages),
            response_window_hours=source.response_window_hours,
            created_by_id=created_by.id,
            tags=list(source.tags),
            steps=[self._copy_step(step) for step in source.steps],
        )
        await self._access.repository.add(duplicate)
        await self._access.commit()
        return series_detail(await self._access.reload(duplicate.id))

    @staticmethod
    def _copy_step(source: SeriesStep) -> SeriesStep:
        return SeriesStep(
            step_order=source.step_order,
            delay_days=source.delay_days,
            category=source.category,
            media_type=source.media_type,
            media_url=source.media_url,
            buttons=deepcopy(source.buttons),
            contents=[
                SeriesStepContent(language=item.language, body=item.body)
                for item in source.contents
            ],
        )

    @staticmethod
    def _validate_existing_buttons(series: ContentSeries, languages: list[LanguageCode]) -> None:
        for step in series.steps:
            buttons = [QuickReplyButtonInput.model_validate(item) for item in step.buttons]
            validate_step_values(languages, [], buttons)
