"""User lookup business logic."""

from app.models.enums import UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserOut, UserPage


class UserService:
    """Return active staff users for coordinator assignment."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def list_active(
        self,
        *,
        role: UserRole | None,
        page: int,
        page_size: int,
    ) -> UserPage:
        """Return a filtered page without exposing password hashes."""
        result = await self._users.list_active(role=role, page=page, page_size=page_size)
        return UserPage(
            items=[UserOut.model_validate(user) for user in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
