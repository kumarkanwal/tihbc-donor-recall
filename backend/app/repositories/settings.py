"""Read-only queries for mocked integration settings."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MessageCategory, SeriesStatus
from app.models.series import ContentSeries, SeriesStep


@dataclass(frozen=True)
class ActiveTemplateRecord:
    """Provider-facing identity for one active content-series step."""

    series_name: str
    step_order: int
    category: MessageCategory


class IntegrationSettingsRepository:
    """Load active steps that are exposed as mocked provider templates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_templates(self) -> tuple[ActiveTemplateRecord, ...]:
        """Return every active step in stable series and step order."""
        statement = (
            select(ContentSeries.name, SeriesStep.step_order, SeriesStep.category)
            .join(SeriesStep, SeriesStep.series_id == ContentSeries.id)
            .where(ContentSeries.status == SeriesStatus.ACTIVE)
            .order_by(ContentSeries.name, SeriesStep.step_order, SeriesStep.id)
        )
        rows = await self._session.execute(statement)
        return tuple(
            ActiveTemplateRecord(
                series_name=series_name,
                step_order=step_order,
                category=category,
            )
            for series_name, step_order, category in rows
        )
