"""Shared transactional access for content-series services."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.enums import SeriesStatus
from app.models.series import ContentSeries, SeriesStep
from app.repositories.content_series import ContentSeriesRepository
from app.services.content_series.validation import activation_problems


class ContentSeriesAccess:
    """Load guarded aggregates and own service-layer transactions."""

    def __init__(self, session: AsyncSession, repository: ContentSeriesRepository) -> None:
        self.session = session
        self.repository = repository

    async def required(self, series_id: UUID) -> ContentSeries:
        """Load one series or raise the domain not-found error."""
        series = await self.repository.get_full(series_id)
        if series is None:
            raise NotFoundError("Content series not found")
        return series

    async def editable(self, series_id: UUID) -> ContentSeries:
        """Load one series after enforcing archive and campaign guards."""
        series = await self.required(series_id)
        if series.status == SeriesStatus.ARCHIVED:
            raise ConflictError("Archived content series cannot be edited")
        if await self.repository.has_edit_blocking_campaign(series_id):
            raise ConflictError("Content series is used by an active campaign")
        return series

    async def reload(self, series_id: UUID) -> ContentSeries:
        """Reload a series known to have been persisted."""
        series = await self.repository.get_full(series_id)
        if series is None:
            raise RuntimeError("Persisted content series could not be reloaded")
        return series

    async def commit(self) -> None:
        """Commit a service operation or roll it back completely."""
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    @staticmethod
    def ensure_active_valid(series: ContentSeries) -> None:
        """Prevent an edit from leaving an active series incomplete."""
        if series.status != SeriesStatus.ACTIVE:
            return
        problems = activation_problems(series)
        if problems:
            raise ValidationError(
                "Edit would invalidate an active content series",
                {"problems": [problem.model_dump(mode="json") for problem in problems]},
            )

    @staticmethod
    def step_by_id(series: ContentSeries, step_id: UUID) -> SeriesStep:
        """Resolve a step inside its parent aggregate."""
        step = next((item for item in series.steps if item.id == step_id), None)
        if step is None:
            raise NotFoundError("Series step not found")
        return step
