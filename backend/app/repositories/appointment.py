"""Database access for appointment-slot booking and seeding."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import AppointmentSlot
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[AppointmentSlot]):
    """Query and persist capacity-limited appointment slots."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AppointmentSlot)

    async def next_available_for_update(
        self,
        *,
        center_name: str,
        starts_at: datetime,
        before: datetime,
    ) -> AppointmentSlot | None:
        """Lock the earliest available slot in the requested two-day window."""
        statement = (
            select(AppointmentSlot)
            .where(
                AppointmentSlot.center_name == center_name,
                AppointmentSlot.starts_at >= starts_at,
                AppointmentSlot.starts_at < before,
                AppointmentSlot.booked_count < AppointmentSlot.capacity,
            )
            .order_by(AppointmentSlot.starts_at, AppointmentSlot.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def existing_keys(
        self,
        *,
        starts_at: datetime,
        before: datetime,
    ) -> set[tuple[str, datetime]]:
        """Return center/time pairs already present in a seed window."""
        rows = await self._session.execute(
            select(AppointmentSlot.center_name, AppointmentSlot.starts_at).where(
                AppointmentSlot.starts_at >= starts_at,
                AppointmentSlot.starts_at < before,
            )
        )
        return {(center, slot_start) for center, slot_start in rows}

    async def get_slot(self, slot_id: UUID) -> AppointmentSlot | None:
        """Return one appointment slot by identifier."""
        return await self.get(slot_id)

    async def add_many(self, slots: list[AppointmentSlot]) -> None:
        """Add slot seed rows to the current transaction."""
        self._session.add_all(slots)
        await self._session.flush()
