"""Database access for coordinator follow-up items."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaign import Enrollment
from app.models.donor import Donor
from app.models.enums import (
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
    MessageDirection,
)
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.models.message import Message
from app.models.response import DonorResponse
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class FollowUpFilters:
    """Database filters shared by inbox views and CSV export."""

    type: FollowUpType | None = None
    status: FollowUpStatus | None = None
    priority: FollowUpPriority | None = None
    campaign_id: UUID | None = None
    assigned_to_id: UUID | None = None
    search: str | None = None


@dataclass(frozen=True)
class FollowUpPageResult:
    items: list[FollowUpItem]
    total: int
    page: int
    page_size: int


class FollowUpRepository(BaseRepository[FollowUpItem]):
    """Persist follow-up items and their audit activities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FollowUpItem)

    async def open_for_enrollment(self, enrollment_id: UUID) -> FollowUpItem | None:
        """Return the current non-completed follow-up, if one exists."""
        statement = select(FollowUpItem).where(
            FollowUpItem.enrollment_id == enrollment_id,
            FollowUpItem.status != FollowUpStatus.DONE,
        )
        return await self._session.scalar(statement)

    async def add_with_activity(
        self,
        item: FollowUpItem,
        activity: FollowUpActivity,
    ) -> None:
        """Add a follow-up and its initial activity in the current transaction."""
        self._session.add_all((item, activity))
        await self._session.flush()

    async def add_activity(self, activity: FollowUpActivity) -> None:
        """Append and flush an activity on an existing follow-up."""
        self._session.add(activity)
        await self._session.flush()

    async def list_filtered(
        self, filters: FollowUpFilters, *, page: int, page_size: int
    ) -> FollowUpPageResult:
        """Return one eagerly loaded filtered page."""
        filtered = self._filtered(select(FollowUpItem), filters)
        total = int(
            await self._session.scalar(self._filtered(select(func.count(FollowUpItem.id)), filters))
            or 0
        )
        statement = (
            self._with_context(filtered)
            .order_by(FollowUpItem.updated_at.desc(), FollowUpItem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await self._session.scalars(statement)).unique().all())
        return FollowUpPageResult(items, total, page, page_size)

    async def list_for_export(self, filters: FollowUpFilters) -> list[FollowUpItem]:
        """Return all matching items for a bounded demo CSV export."""
        statement = self._with_context(self._filtered(select(FollowUpItem), filters)).order_by(
            FollowUpItem.updated_at.desc(), FollowUpItem.id.desc()
        )
        return list((await self._session.scalars(statement)).unique().all())

    async def summary(
        self, filters: FollowUpFilters
    ) -> tuple[int, dict[FollowUpType, int], dict[FollowUpStatus, int]]:
        """Return total and grouped counts for the inbox tabs."""
        base = self._filtered(select(FollowUpItem), filters)
        subquery = base.with_only_columns(
            FollowUpItem.id, FollowUpItem.type, FollowUpItem.status
        ).subquery()
        total = int(await self._session.scalar(select(func.count()).select_from(subquery)) or 0)
        by_type_rows = await self._session.execute(
            select(subquery.c.type, func.count()).group_by(subquery.c.type)
        )
        by_status_rows = await self._session.execute(
            select(subquery.c.status, func.count()).group_by(subquery.c.status)
        )
        return total, dict(by_type_rows.all()), dict(by_status_rows.all())

    async def get_full(self, item_id: UUID, *, for_update: bool = False) -> FollowUpItem | None:
        """Load one complete aggregate, optionally locking its item row."""
        statement = self._with_context(select(FollowUpItem).where(FollowUpItem.id == item_id))
        if for_update:
            statement = statement.with_for_update(of=FollowUpItem)
        item: FollowUpItem | None = (await self._session.scalars(statement)).unique().one_or_none()
        return item

    @staticmethod
    def _filtered[RowT](statement: Select[RowT], filters: FollowUpFilters) -> Select[RowT]:
        statement = statement.join(FollowUpItem.enrollment).join(Enrollment.donor)
        if filters.type:
            statement = statement.where(FollowUpItem.type == filters.type)
        if filters.status:
            statement = statement.where(FollowUpItem.status == filters.status)
        if filters.priority:
            statement = statement.where(FollowUpItem.priority == filters.priority)
        if filters.campaign_id:
            statement = statement.where(Enrollment.campaign_id == filters.campaign_id)
        if filters.assigned_to_id:
            statement = statement.where(FollowUpItem.assigned_to_id == filters.assigned_to_id)
        if filters.search and (term := filters.search.strip()):
            pattern = f"%{term}%"
            reply_match = exists().where(
                Message.enrollment_id == Enrollment.id,
                Message.direction == MessageDirection.INBOUND,
                Message.body.ilike(pattern),
            )
            statement = statement.where(
                or_(Donor.full_name.ilike(pattern), Donor.phone_e164.ilike(pattern), reply_match)
            )
        return statement

    @staticmethod
    def _with_context(
        statement: Select[FollowUpItem],
    ) -> Select[FollowUpItem]:
        enrollment = selectinload(FollowUpItem.enrollment)
        return statement.options(
            selectinload(FollowUpItem.assigned_to),
            selectinload(FollowUpItem.activities).selectinload(FollowUpActivity.user),
            enrollment.selectinload(Enrollment.campaign),
            enrollment.selectinload(Enrollment.donor).selectinload(Donor.segment),
            enrollment.selectinload(Enrollment.messages),
            enrollment.selectinload(Enrollment.responses).selectinload(DonorResponse.message),
            enrollment.selectinload(Enrollment.appointment_slot),
        ).execution_options(populate_existing=True)
