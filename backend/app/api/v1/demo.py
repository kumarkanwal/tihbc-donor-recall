"""Demo-clock API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_demo_clock_service, require_role
from app.models.enums import UserRole
from app.schemas.demo import DemoClockAdvance, DemoClockOut
from app.schemas.user import UserOut
from app.services.demo_clock import DemoClockService

router = APIRouter(prefix="/demo/clock", tags=["Demo"])
admin_access = require_role(UserRole.ADMIN)
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


@router.get("", response_model=DemoClockOut, summary="Get the demo clock")
async def get_demo_clock(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[DemoClockService, Depends(get_demo_clock_service)],
) -> DemoClockOut:
    """Return the current demo time and offset."""
    del current_user
    return service.get()


@router.post(
    "/actions/advance",
    response_model=DemoClockOut,
    summary="Advance the demo clock",
)
async def advance_demo_clock(
    request: DemoClockAdvance,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[DemoClockService, Depends(get_demo_clock_service)],
) -> DemoClockOut:
    """Advance the demo clock and immediately run one scheduler tick."""
    del current_user
    return await service.advance(request)


@router.post(
    "/actions/reset",
    response_model=DemoClockOut,
    summary="Reset the demo clock",
)
async def reset_demo_clock(
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[DemoClockService, Depends(get_demo_clock_service)],
) -> DemoClockOut:
    """Reset the demo clock offset to zero."""
    del current_user
    return await service.reset()
