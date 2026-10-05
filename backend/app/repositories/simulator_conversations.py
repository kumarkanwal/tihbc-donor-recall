"""Bounded donor-thread previews without per-row message lookups."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, Enrollment
from app.models.donor import Donor
from app.models.enums import MessageDirection, MessageStatus
from app.models.message import Message
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class ConversationRecord:
    """Latest matching message and campaign context for one donor."""

    donor: Donor
    message: Message
    campaign_id: UUID | None
    campaign_name: str | None
    unread_count: int


class ConversationRepository(BaseRepository[Donor]):
    """Query thread previews in one query plus the pagination count."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Donor)

    async def list_threads(
        self,
        *,
        campaign_id: UUID | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[tuple[ConversationRecord, ...], int]:
        matching = [Message.donor_id == Donor.id]
        if campaign_id is not None:
            matching.append(
                Message.enrollment_id.in_(
                    select(Enrollment.id).where(Enrollment.campaign_id == campaign_id)
                )
            )
        latest = (
            select(Message.id)
            .where(*matching)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
            .correlate(Donor)
            .scalar_subquery()
        )
        unread = (
            select(func.count(Message.id))
            .where(
                *matching,
                Message.direction == MessageDirection.OUTBOUND,
                Message.status == MessageStatus.DELIVERED,
            )
            .correlate(Donor)
            .scalar_subquery()
        )
        filters = []
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(or_(Donor.full_name.ilike(term), Donor.phone_e164.ilike(term)))
        statement = (
            select(Donor, Message, Enrollment.campaign_id, Campaign.name, unread)
            .select_from(Donor)
            .join(Message, Message.id == latest)
            .outerjoin(Enrollment, Message.enrollment_id == Enrollment.id)
            .outerjoin(Campaign, Enrollment.campaign_id == Campaign.id)
            .where(*filters)
            .order_by(Message.created_at.desc(), Donor.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count = select(func.count(Donor.id)).where(
            *filters,
            select(Message.id).where(*matching).correlate(Donor).exists(),
        )
        rows = await self._session.execute(statement)
        return tuple(
            ConversationRecord(
                *cast(tuple[Donor, Message, UUID | None, str | None, int], tuple(row))
            )
            for row in rows
        ), int(await self._session.scalar(count) or 0)
