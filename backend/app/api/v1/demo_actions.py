"""Administrator-only demo environment actions."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_demo_reset_service, require_role
from app.models.enums import UserRole
from app.schemas.user import UserOut
from app.services.demo_reset import DemoResetService

router = APIRouter(prefix="/demo/actions", tags=["Demo"])
admin_access = require_role(UserRole.ADMIN)


@router.post(
    "/reset-data",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset demo data",
)
async def reset_demo_data(
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[DemoResetService, Depends(get_demo_reset_service)],
) -> Response:
    """Clear operational demo data and rebuild the complete seeded dataset."""
    del current_user
    await service.reset()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
