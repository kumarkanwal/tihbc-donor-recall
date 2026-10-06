"""Database reset operations for the guarded demo action."""

from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

RESET_ROOT_TABLES = (
    "donor_batches",
    "content_series",
    "appointment_slots",
    "segments",
    "tags",
)
RESET_STATEMENT: TextClause = text(
    "TRUNCATE TABLE donor_batches, content_series, appointment_slots, segments, tags CASCADE"
)


class DemoResetRepository:
    """Clear operational demo aggregates while retaining staff and clock state."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def truncate_demo_data(self) -> None:
        """Transactionally clear all data rooted in the demo aggregates."""
        await self._session.execute(RESET_STATEMENT)
