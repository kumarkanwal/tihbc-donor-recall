"""Simulator message reads, reply context, and row-locked read receipts."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import MessageDirection, MessageStatus
from app.models.message import Message
from app.repositories.base import BaseRepository


class SimulatorMessageRepository(BaseRepository[Message]):
    """Queries for one donor's message history."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)

    async def visible_page(
        self,
        donor_id: UUID,
        *,
        before: tuple[datetime, UUID] | None,
        limit: int,
    ) -> tuple[Message, ...]:
        statement = select(Message).where(
            Message.donor_id == donor_id,
            Message.status != MessageStatus.FAILED,
        )
        if before is not None:
            statement = statement.where(tuple_(Message.created_at, Message.id) < tuple_(*before))
        statement = statement.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
        return tuple(await self._session.scalars(statement))

    async def latest_outbound(self, donor_id: UUID) -> Message | None:
        """Select the enrollment context of a donor's most recent sent outreach."""
        return await self._session.scalar(
            select(Message)
            .where(
                Message.donor_id == donor_id,
                Message.direction == MessageDirection.OUTBOUND,
                Message.status.in_(
                    (MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.READ)
                ),
                Message.enrollment_id.is_not(None),
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
        )

    async def has_reply(self, message_id: UUID) -> bool:
        """Return whether a button-bearing message has already received a reply."""
        return (
            await self._session.scalar(
                select(Message.id)
                .where(
                    Message.reply_to_message_id == message_id,
                    Message.direction == MessageDirection.INBOUND,
                )
                .limit(1)
            )
            is not None
        )

    async def delivered_outbound_for_update(self, donor_id: UUID) -> tuple[Message, ...]:
        """Lock only delivered outbound rows; coordinate with delivery progression."""
        statement = (
            select(Message)
            .where(
                Message.donor_id == donor_id,
                Message.direction == MessageDirection.OUTBOUND,
                Message.status == MessageStatus.DELIVERED,
            )
            .order_by(Message.created_at, Message.id)
            .with_for_update(of=Message)
            .options(selectinload(Message.enrollment))
        )
        return tuple(await self._session.scalars(statement))
