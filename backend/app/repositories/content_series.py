"""Database access for content series, steps, tags, and edit guards."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import ScalarSelect

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus, LanguageCode, SeriesKind, SeriesStatus
from app.models.series import ContentSeries, SeriesStep, Tag
from app.repositories.base import BaseRepository

EDIT_BLOCKING_CAMPAIGN_STATUSES = (
    CampaignStatus.SCHEDULED,
    CampaignStatus.RUNNING,
    CampaignStatus.PAUSED,
)


@dataclass(frozen=True)
class ContentSeriesRecord:
    """A loaded series and its database-computed step count."""

    series: ContentSeries
    step_count: int


@dataclass(frozen=True)
class ContentSeriesRecordPage:
    """One page of loaded content-series records."""

    items: tuple[ContentSeriesRecord, ...]
    total: int
    page: int
    page_size: int


class ContentSeriesRepository(BaseRepository[ContentSeries]):
    """Query and persist the content-series aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ContentSeries)

    async def list_filtered(
        self,
        *,
        kind: SeriesKind | None,
        status: SeriesStatus | None,
        tag: str | None,
        language: LanguageCode | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> ContentSeriesRecordPage:
        """Return a filtered page with uploader and tags loaded."""
        filters = self._filters(kind, status, tag, language, search)
        step_count: ScalarSelect[int] = (
            select(func.count(SeriesStep.id))
            .where(SeriesStep.series_id == ContentSeries.id)
            .correlate(ContentSeries)
            .scalar_subquery()
        )
        statement = (
            select(ContentSeries, step_count)
            .options(
                selectinload(ContentSeries.created_by),
                selectinload(ContentSeries.tags),
            )
            .where(*filters)
            .order_by(ContentSeries.updated_at.desc(), ContentSeries.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count()).select_from(ContentSeries).where(*filters)
        rows = await self._session.execute(statement)
        total = await self._session.scalar(count_statement)
        return ContentSeriesRecordPage(
            items=tuple(ContentSeriesRecord(series=item, step_count=count) for item, count in rows),
            total=total or 0,
            page=page,
            page_size=page_size,
        )

    async def get_full(self, series_id: UUID) -> ContentSeries | None:
        """Return one series with all detail relationships loaded."""
        statement = (
            select(ContentSeries)
            .execution_options(populate_existing=True)
            .options(
                selectinload(ContentSeries.created_by),
                selectinload(ContentSeries.tags),
                selectinload(ContentSeries.steps).selectinload(SeriesStep.contents),
            )
            .where(ContentSeries.id == series_id)
        )
        return await self._session.scalar(statement)

    async def get_or_create_tags(self, names: list[str]) -> list[Tag]:
        """Resolve normalized tag names, creating missing rows."""
        tags: list[Tag] = []
        for name in names:
            normalized = name.strip().casefold()
            tag = await self._session.scalar(select(Tag).where(func.lower(Tag.name) == normalized))
            if tag is None:
                tag = Tag(name=normalized)
                self._session.add(tag)
                await self._session.flush()
            tags.append(tag)
        return tags

    async def has_edit_blocking_campaign(self, series_id: UUID) -> bool:
        """Return whether a scheduled or live campaign references the series."""
        statement = select(
            exists().where(
                or_(
                    Campaign.primary_series_id == series_id,
                    Campaign.secondary_series_id == series_id,
                ),
                Campaign.status.in_(EDIT_BLOCKING_CAMPAIGN_STATUSES),
            )
        )
        return bool(await self._session.scalar(statement))

    async def reorder_steps(self, series_id: UUID, ordered_ids: list[UUID]) -> None:
        """Persist a complete collision-free contiguous step order."""
        offset = len(ordered_ids) + 1
        move_statement = (
            update(SeriesStep)
            .where(SeriesStep.series_id == series_id)
            .values(step_order=SeriesStep.step_order + offset)
            .execution_options(synchronize_session=False)
        )
        await self._session.execute(move_statement)
        for step_order, step_id in enumerate(ordered_ids, start=1):
            statement = (
                update(SeriesStep)
                .where(SeriesStep.id == step_id, SeriesStep.series_id == series_id)
                .values(step_order=step_order)
                .execution_options(synchronize_session=False)
            )
            await self._session.execute(statement)

    @staticmethod
    def _filters(
        kind: SeriesKind | None,
        status: SeriesStatus | None,
        tag: str | None,
        language: LanguageCode | None,
        search: str | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []
        if kind is not None:
            filters.append(ContentSeries.kind == kind)
        if status is not None:
            filters.append(ContentSeries.status == status)
        if tag and tag.strip():
            filters.append(ContentSeries.tags.any(func.lower(Tag.name) == tag.strip().casefold()))
        if language is not None:
            filters.append(ContentSeries.languages.contains([language]))
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(ContentSeries.name.ilike(term), ContentSeries.description.ilike(term))
            )
        return filters
