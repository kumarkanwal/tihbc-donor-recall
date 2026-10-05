"""Database access for outbound messages and delivery progression."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.donor import Donor
from app.models.enums import MessageStatus
from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Persist messages and lock due delivery transitions."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)

    async def add_message(self, message: Message) -> None:
        """Add and flush one message in the current transaction."""
        await self.add(message)

    async def exists_for_step(self, enrollment_id: UUID, step_id: UUID) -> bool:
        """Return whether an enrollment already has a message for a series step."""
        statement = select(Message.id).where(
            Message.enrollment_id == enrollment_id,
            Message.step_id == step_id,
        )
        return await self._session.scalar(statement) is not None

    async def sent_due_for_delivery(self, cutoff: datetime) -> tuple[Message, ...]:
        """Lock sent messages whose simulated delivery delay elapsed."""
        return await self._due_messages(
            Message.status == MessageStatus.SENT,
            Message.sent_at.is_not(None),
            Message.sent_at <= cutoff,
        )

    async def delivered_due_for_read(self, cutoff: datetime) -> tuple[Message, ...]:
        """Lock delivered messages eligible for simulated read receipts."""
        return await self._due_messages(
            Message.status == MessageStatus.DELIVERED,
            Message.delivered_at.is_not(None),
            Message.delivered_at <= cutoff,
            Donor.sim_read_receipts.is_(True),
        )

    async def _due_messages(self, *filters: ColumnElement[bool]) -> tuple[Message, ...]:
        statement = (
            select(Message)
            .join(Donor, Message.donor_id == Donor.id)
            .where(*filters)
            .order_by(Message.created_at, Message.id)
            .with_for_update(skip_locked=True)
            .options(selectinload(Message.donor), selectinload(Message.enrollment))
        )
        messages = await self._session.scalars(statement)
        return tuple(messages.all())
