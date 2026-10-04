"""Campaign lifecycle and enrollment routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_campaign_query_service, get_campaign_service, require_role
from app.models.enums import CampaignStatus, EnrollmentStatus, UserRole
from app.schemas.campaign import (
    CampaignCreate,
    CampaignDetail,
    CampaignPage,
    CampaignUpdate,
    EnrollmentDetail,
    EnrollmentPage,
)
from app.schemas.user import UserOut
from app.services.campaigns.query_service import CampaignQueryService
from app.services.campaigns.service import CampaignService

campaign_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
enrollment_router = APIRouter(prefix="/enrollments", tags=["Enrollments"])
admin_access = require_role(UserRole.ADMIN)
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


@campaign_router.get("", response_model=CampaignPage, summary="List campaigns")
async def list_campaigns(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[CampaignQueryService, Depends(get_campaign_query_service)],
    status_filter: Annotated[CampaignStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CampaignPage:
    """Return a status-filtered campaign page."""
    del current_user
    return await service.list_campaigns(
        status=status_filter,
        page=page,
        page_size=page_size,
    )


@campaign_router.post(
    "",
    response_model=CampaignDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a campaign",
)
async def create_campaign(
    request: CampaignCreate,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignDetail:
    """Create one draft campaign."""
    return await service.create(request, current_user)


@campaign_router.get(
    "/{campaign_id}",
    response_model=CampaignDetail,
    summary="Get campaign details",
)
async def get_campaign(
    campaign_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[CampaignQueryService, Depends(get_campaign_query_service)],
) -> CampaignDetail:
    """Return one campaign with enrollment-status counts."""
    del current_user
    return await service.get_campaign(campaign_id)


@campaign_router.patch(
    "/{campaign_id}",
    response_model=CampaignDetail,
    summary="Update a draft campaign",
)
async def update_campaign(
    campaign_id: UUID,
    request: CampaignUpdate,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignDetail:
    """Update selected fields on a draft campaign."""
    del current_user
    return await service.update(campaign_id, request)


@campaign_router.post(
    "/{campaign_id}/actions/launch",
    response_model=CampaignDetail,
    summary="Launch a campaign",
)
async def launch_campaign(
    campaign_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignDetail:
    """Validate a draft and create its donor enrollments."""
    del current_user
    return await service.launch(campaign_id)


@campaign_router.post(
    "/{campaign_id}/actions/pause",
    response_model=CampaignDetail,
    summary="Pause a campaign",
)
async def pause_campaign(
    campaign_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignDetail:
    """Pause a running campaign."""
    del current_user
    return await service.pause(campaign_id)


@campaign_router.post(
    "/{campaign_id}/actions/resume",
    response_model=CampaignDetail,
    summary="Resume a campaign",
)
async def resume_campaign(
    campaign_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignDetail:
    """Resume a paused campaign."""
    del current_user
    return await service.resume(campaign_id)


@campaign_router.get(
    "/{campaign_id}/enrollments",
    response_model=EnrollmentPage,
    summary="List campaign enrollments",
)
async def list_campaign_enrollments(
    campaign_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[CampaignQueryService, Depends(get_campaign_query_service)],
    status_filter: Annotated[EnrollmentStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EnrollmentPage:
    """Return filtered enrollments with masked list phone values."""
    del current_user
    return await service.list_enrollments(
        campaign_id,
        status=status_filter,
        search=search,
        page=page,
        page_size=page_size,
    )


@enrollment_router.get(
    "/{enrollment_id}",
    response_model=EnrollmentDetail,
    summary="Get enrollment details",
)
async def get_enrollment(
    enrollment_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[CampaignQueryService, Depends(get_campaign_query_service)],
) -> EnrollmentDetail:
    """Return a full donor enrollment timeline and follow-up."""
    del current_user
    return await service.get_enrollment(enrollment_id)
