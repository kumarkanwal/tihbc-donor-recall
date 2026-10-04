"""User API schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserOut(BaseModel):
    """Public staff-user fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool


class UserPage(BaseModel):
    """Paginated active-user response."""

    items: list[UserOut]
    total: int
    page: int
    page_size: int
