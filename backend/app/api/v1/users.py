"""Staff user lookup API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_user_service, require_role
from app.models.enums import UserRole
from app.schemas.user import UserOut, UserPage
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


@router.get(
    "",
    response_model=UserPage,
    summary="List active staff users",
)
async def list_users(
    current_user: Annotated[UserOut, Depends(staff_access)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    role: Annotated[UserRole | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserPage:
    """Return active users, optionally filtered by role."""
    del current_user
    return await user_service.list_active(role=role, page=page, page_size=page_size)
