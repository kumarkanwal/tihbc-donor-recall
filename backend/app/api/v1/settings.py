"""Mocked messaging integration settings routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_integration_settings_service, require_role
from app.models.enums import UserRole
from app.schemas.settings import IntegrationSettingsOut
from app.schemas.user import UserOut
from app.services.settings_service import IntegrationSettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


@router.get(
    "/integration",
    response_model=IntegrationSettingsOut,
    summary="Get mocked messaging integration settings",
)
async def get_integration_settings(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[
        IntegrationSettingsService,
        Depends(get_integration_settings_service),
    ],
) -> IntegrationSettingsOut:
    """Return provider status and templates derived from active series steps."""
    del current_user
    return await service.get()
