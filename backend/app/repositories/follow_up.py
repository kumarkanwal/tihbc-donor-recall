"""Database access for coordinator follow-up items."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import FollowUpStatus
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.repositories.base import BaseRepository


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
