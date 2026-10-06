"""Coordinator follow-up inbox routes."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_follow_up_service, require_role
from app.models.enums import FollowUpPriority, FollowUpStatus, FollowUpType, UserRole
from app.repositories.follow_up import FollowUpFilters
from app.schemas.follow_up import (
    FollowUpDetail,
    FollowUpInboxSummary,
    FollowUpNoteCreate,
    FollowUpPage,
    FollowUpResolve,
    FollowUpUpdate,
)
from app.schemas.user import UserOut
from app.services.follow_ups.service import FollowUpService

router = APIRouter(prefix="/follow-ups", tags=["Follow-ups"])
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


def _filters(
    current_user: UserOut,
    type_filter: FollowUpType | None,
    status_filter: FollowUpStatus | None,
    priority: FollowUpPriority | None,
    campaign_id: UUID | None,
    assigned_to: Literal["me"] | None,
    search: str | None,
) -> FollowUpFilters:
    return FollowUpFilters(
        type=type_filter,
        status=status_filter,
        priority=priority,
        campaign_id=campaign_id,
        assigned_to_id=current_user.id if assigned_to == "me" else None,
        search=search,
    )


@router.get("", response_model=FollowUpPage, summary="List follow-ups")
async def list_follow_ups(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
    type_filter: Annotated[FollowUpType | None, Query(alias="type")] = None,
    status_filter: Annotated[FollowUpStatus | None, Query(alias="status")] = None,
    priority: FollowUpPriority | None = None,
    campaign_id: UUID | None = None,
    assigned_to: Literal["me"] | None = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FollowUpPage:
    """Return a filtered coordinator work queue."""
    return await service.list(
        _filters(
            current_user, type_filter, status_filter, priority, campaign_id, assigned_to, search
        ),
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=FollowUpInboxSummary, summary="Summarize follow-ups")
async def summarize_follow_ups(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
    type_filter: Annotated[FollowUpType | None, Query(alias="type")] = None,
    status_filter: Annotated[FollowUpStatus | None, Query(alias="status")] = None,
    priority: FollowUpPriority | None = None,
    campaign_id: UUID | None = None,
    assigned_to: Literal["me"] | None = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
) -> FollowUpInboxSummary:
    """Return type and status counts under the supplied filters."""
    return await service.summary(
        _filters(
            current_user, type_filter, status_filter, priority, campaign_id, assigned_to, search
        )
    )


@router.get("/export", summary="Export follow-ups")
async def export_follow_ups(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
    type_filter: Annotated[FollowUpType | None, Query(alias="type")] = None,
    status_filter: Annotated[FollowUpStatus | None, Query(alias="status")] = None,
    priority: FollowUpPriority | None = None,
    campaign_id: UUID | None = None,
    assigned_to: Literal["me"] | None = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
) -> Response:
    """Download matching work items as CSV."""
    content = await service.export_csv(
        _filters(
            current_user, type_filter, status_filter, priority, campaign_id, assigned_to, search
        )
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="tihbc-follow-ups.csv"'},
    )


@router.get("/{item_id}", response_model=FollowUpDetail, summary="Get follow-up details")
async def get_follow_up(
    item_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpDetail:
    """Return donor, response, appointment, and activity context."""
    del current_user
    return await service.get(item_id)


@router.patch("/{item_id}", response_model=FollowUpDetail, summary="Update a follow-up")
async def update_follow_up(
    item_id: UUID,
    request: FollowUpUpdate,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpDetail:
    """Change status, assignee, or priority with audit activities."""
    return await service.update(item_id, request, current_user)


@router.post("/{item_id}/notes", response_model=FollowUpDetail, summary="Add a follow-up note")
async def add_follow_up_note(
    item_id: UUID,
    request: FollowUpNoteCreate,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpDetail:
    """Append one coordinator note."""
    return await service.add_note(item_id, request, current_user)


@router.post(
    "/{item_id}/actions/resolve",
    response_model=FollowUpDetail,
    summary="Resolve a follow-up",
)
async def resolve_follow_up(
    item_id: UUID,
    request: FollowUpResolve,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpDetail:
    """Complete one item with an outcome and optional note."""
    return await service.resolve(item_id, request, current_user)
