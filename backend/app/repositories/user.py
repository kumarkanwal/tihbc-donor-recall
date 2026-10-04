"""User database queries."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository, Page


class UserRepository(BaseRepository[User]):
    """Query staff users without applying authentication rules."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by case-insensitive email."""
        statement = select(User).where(func.lower(User.email) == email.strip().lower())
        return await self._session.scalar(statement)

    async def list_active(
        self,
        *,
        role: UserRole | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[User]:
        """Return active users, optionally filtered by role."""
        statement = select(User).where(User.is_active.is_(True))
        count_statement = select(func.count()).select_from(User).where(User.is_active.is_(True))
        if role is not None:
            statement = statement.where(User.role == role)
            count_statement = count_statement.where(User.role == role)
        statement = (
            statement.order_by(User.full_name, User.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(statement)
        total = await self._session.scalar(count_statement)
        return Page(
            items=tuple(result.scalars().all()),
            total=total or 0,
            page=page,
            page_size=page_size,
        )
