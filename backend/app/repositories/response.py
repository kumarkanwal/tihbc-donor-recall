"""Queries for classified donor responses."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ResponseIntent
from app.models.response import DonorResponse
from app.repositories.base import BaseRepository


class DonorResponseRepository(BaseRepository[DonorResponse]):
    """Persist and count structured donor responses."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DonorResponse)

    async def unknown_count(self, enrollment_id: UUID) -> int:
        """Count unclear replies for one enrollment, including pending changes."""
        count = await self._session.scalar(
            select(func.count(DonorResponse.id)).where(
                DonorResponse.enrollment_id == enrollment_id,
                DonorResponse.intent == ResponseIntent.UNKNOWN,
            )
        )
        return count or 0
