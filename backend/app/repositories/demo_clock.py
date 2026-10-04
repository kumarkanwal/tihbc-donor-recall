"""Persistence adapter for the singleton demo clock row."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.demo_clock import DemoClock
from app.repositories.base import BaseRepository

DEMO_CLOCK_ID = 1


class DemoClockRepository(BaseRepository[DemoClock]):
    """Query and update the persisted demo clock."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DemoClock)

    async def get_for_update(self) -> DemoClock | None:
        """Return the singleton row with a transaction-scoped row lock."""
        statement = select(DemoClock).where(DemoClock.id == DEMO_CLOCK_ID).with_for_update()
        return await self._session.scalar(statement)


class DatabaseClockPersistence:
    """Persist clock changes through short, atomic transactions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def load_offset_seconds(self) -> int:
        """Load the persisted offset."""
        async with self._session_factory() as session:
            row = await DemoClockRepository(session).get(DEMO_CLOCK_ID)
            return self._require_row(row).offset_seconds

    async def increment_offset_seconds(self, seconds: int) -> int:
        """Atomically increment and return the persisted offset."""
        async with self._session_factory.begin() as session:
            repository = DemoClockRepository(session)
            row = self._require_row(await repository.get_for_update())
            row.offset_seconds += seconds
            await session.flush()
            return row.offset_seconds

    async def set_offset_seconds(self, seconds: int) -> int:
        """Atomically replace and return the persisted offset."""
        async with self._session_factory.begin() as session:
            repository = DemoClockRepository(session)
            row = self._require_row(await repository.get_for_update())
            row.offset_seconds = seconds
            await session.flush()
            return row.offset_seconds

    @staticmethod
    def _require_row(row: DemoClock | None) -> DemoClock:
        if row is None:
            raise RuntimeError("Demo clock row is missing; apply database migrations")
        return row
