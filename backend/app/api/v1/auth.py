"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with staff credentials",
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate a staff user and issue an access token."""
    return await auth_service.authenticate(request)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get the current staff user",
)
async def get_me(current_user: Annotated[UserOut, Depends(get_current_user)]) -> UserOut:
    """Return the authenticated active user."""
    return current_user
