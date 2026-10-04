"""Donor batch database queries."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import LanguageCode
from app.models.user import User
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class BatchSummaryRecord:
    """A batch with uploader identity and campaign count."""

    batch: DonorBatch
    uploaded_by: User
    campaign_count: int


@dataclass(frozen=True)
class BatchRecordPage:
    """One page of batch summary records."""

    items: tuple[BatchSummaryRecord, ...]
    total: int
    page: int
    page_size: int


class DonorBatchRepository(BaseRepository[DonorBatch]):
    """Query donor batches and database-computed breakdowns."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DonorBatch)

    async def list_with_summary(
        self,
        *,
        search: str | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> BatchRecordPage:
        """Return searchable batch summaries."""
        filters = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    DonorBatch.name.ilike(term),
                    DonorBatch.original_filename.ilike(term),
                    User.full_name.ilike(term),
                )
            )
        order_column = (
            DonorBatch.name if sort.removeprefix("-") == "name" else DonorBatch.created_at
        )
        order_by = order_column.desc() if sort.startswith("-") else order_column.asc()
        statement = (
            select(DonorBatch, User, func.count(Campaign.id))
            .join(User, DonorBatch.uploaded_by_id == User.id)
            .outerjoin(Campaign, Campaign.batch_id == DonorBatch.id)
            .where(*filters)
            .group_by(DonorBatch.id, User.id)
            .order_by(order_by, DonorBatch.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = (
            select(func.count())
            .select_from(DonorBatch)
            .join(User, DonorBatch.uploaded_by_id == User.id)
            .where(*filters)
        )
        rows = await self._session.execute(statement)
        total = await self._session.scalar(count_statement)
        return BatchRecordPage(
            items=tuple(
                BatchSummaryRecord(batch=batch, uploaded_by=user, campaign_count=campaign_count)
                for batch, user, campaign_count in rows
            ),
            total=total or 0,
            page=page,
            page_size=page_size,
        )

    async def get_with_summary(self, batch_id: UUID) -> BatchSummaryRecord | None:
        """Return one batch summary by ID."""
        statement = (
            select(DonorBatch, User, func.count(Campaign.id))
            .join(User, DonorBatch.uploaded_by_id == User.id)
            .outerjoin(Campaign, Campaign.batch_id == DonorBatch.id)
            .where(DonorBatch.id == batch_id)
            .group_by(DonorBatch.id, User.id)
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        batch, user, campaign_count = row
        return BatchSummaryRecord(
            batch=batch,
            uploaded_by=user,
            campaign_count=campaign_count,
        )

    async def segment_breakdown(self, batch_id: UUID) -> tuple[tuple[str, int], ...]:
        """Count imported donors by segment."""
        statement = (
            select(Segment.key, func.count(Donor.id))
            .join(Donor, Donor.segment_id == Segment.id)
            .where(Donor.batch_id == batch_id)
            .group_by(Segment.key)
            .order_by(Segment.key)
        )
        return tuple((key, count) for key, count in await self._session.execute(statement))

    async def language_breakdown(self, batch_id: UUID) -> tuple[tuple[LanguageCode, int], ...]:
        """Count imported donors by language."""
        statement = (
            select(Donor.language, func.count(Donor.id))
            .where(Donor.batch_id == batch_id)
            .group_by(Donor.language)
            .order_by(Donor.language)
        )
        return tuple(
            (language, count) for language, count in await self._session.execute(statement)
        )
