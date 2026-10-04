"""Content-series library, editor, lifecycle, and preview routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_content_series_query_service,
    get_content_series_service,
    get_series_step_service,
    require_role,
)
from app.models.enums import LanguageCode, SeriesKind, SeriesStatus, UserRole
from app.schemas.content_series import (
    ContentSeriesCreate,
    ContentSeriesDetail,
    ContentSeriesPage,
    ContentSeriesUpdate,
    SeriesPreviewInput,
    SeriesPreviewMessage,
    SeriesReorderInput,
    SeriesStepInput,
    SeriesStepOut,
    SeriesStepUpdate,
)
from app.schemas.user import UserOut
from app.services.content_series.query_service import ContentSeriesQueryService
from app.services.content_series.service import ContentSeriesService
from app.services.content_series.step_service import SeriesStepService

router = APIRouter(prefix="/content-series", tags=["Content Series"])
admin_access = require_role(UserRole.ADMIN)
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


@router.get("", response_model=ContentSeriesPage, summary="List content series")
async def list_content_series(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[ContentSeriesQueryService, Depends(get_content_series_query_service)],
    kind: Annotated[SeriesKind | None, Query()] = None,
    status_filter: Annotated[SeriesStatus | None, Query(alias="status")] = None,
    tag: Annotated[str | None, Query(max_length=40)] = None,
    language: Annotated[LanguageCode | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ContentSeriesPage:
    """Return filtered content-series summaries."""
    del current_user
    return await service.list_series(
        kind=kind,
        status=status_filter,
        tag=tag,
        language=language,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=ContentSeriesDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a content series",
)
async def create_content_series(
    request: ContentSeriesCreate,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[ContentSeriesService, Depends(get_content_series_service)],
) -> ContentSeriesDetail:
    """Create one draft content series."""
    return await service.create(request, current_user)


@router.get(
    "/{series_id}",
    response_model=ContentSeriesDetail,
    summary="Get content-series details",
)
async def get_content_series(
    series_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[ContentSeriesQueryService, Depends(get_content_series_query_service)],
) -> ContentSeriesDetail:
    """Return one series with ordered steps and contents."""
    del current_user
    return await service.get_series(series_id)


@router.patch(
    "/{series_id}",
    response_model=ContentSeriesDetail,
    summary="Update a content series",
)
async def update_content_series(
    series_id: UUID,
    request: ContentSeriesUpdate,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[ContentSeriesService, Depends(get_content_series_service)],
) -> ContentSeriesDetail:
    """Update editable series settings."""
    del current_user
    return await service.update(series_id, request)


@router.post(
    "/{series_id}/actions/activate",
    response_model=ContentSeriesDetail,
    summary="Activate a content series",
)
async def activate_content_series(
    series_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[ContentSeriesService, Depends(get_content_series_service)],
) -> ContentSeriesDetail:
    """Validate every step and activate the series."""
    del current_user
    return await service.activate(series_id)


@router.post(
    "/{series_id}/actions/archive",
    response_model=ContentSeriesDetail,
    summary="Archive a content series",
)
async def archive_content_series(
    series_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[ContentSeriesService, Depends(get_content_series_service)],
) -> ContentSeriesDetail:
    """Archive a series not used by an active campaign."""
    del current_user
    return await service.archive(series_id)


@router.post(
    "/{series_id}/actions/duplicate",
    response_model=ContentSeriesDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate a content series",
)
async def duplicate_content_series(
    series_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[ContentSeriesService, Depends(get_content_series_service)],
) -> ContentSeriesDetail:
    """Deep-copy a series into a new draft."""
    return await service.duplicate(series_id, current_user)


@router.post(
    "/{series_id}/steps",
    response_model=SeriesStepOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a content-series step",
)
async def create_series_step(
    series_id: UUID,
    request: SeriesStepInput,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[SeriesStepService, Depends(get_series_step_service)],
) -> SeriesStepOut:
    """Append a validated step to a series."""
    del current_user
    return await service.create_step(series_id, request)


@router.post(
    "/{series_id}/steps/actions/reorder",
    response_model=ContentSeriesDetail,
    summary="Reorder content-series steps",
)
async def reorder_series_steps(
    series_id: UUID,
    request: SeriesReorderInput,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[SeriesStepService, Depends(get_series_step_service)],
) -> ContentSeriesDetail:
    """Replace the complete step order."""
    del current_user
    return await service.reorder_steps(series_id, request)


@router.patch(
    "/{series_id}/steps/{step_id}",
    response_model=SeriesStepOut,
    summary="Update a content-series step",
)
async def update_series_step(
    series_id: UUID,
    step_id: UUID,
    request: SeriesStepUpdate,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[SeriesStepService, Depends(get_series_step_service)],
) -> SeriesStepOut:
    """Update one step without changing its order."""
    del current_user
    return await service.update_step(series_id, step_id, request)


@router.delete(
    "/{series_id}/steps/{step_id}",
    response_model=ContentSeriesDetail,
    summary="Delete a content-series step",
)
async def delete_series_step(
    series_id: UUID,
    step_id: UUID,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[SeriesStepService, Depends(get_series_step_service)],
) -> ContentSeriesDetail:
    """Delete a step and return the renumbered series."""
    del current_user
    return await service.delete_step(series_id, step_id)


@router.post(
    "/{series_id}/preview",
    response_model=SeriesPreviewMessage,
    summary="Preview a rendered series step",
)
async def preview_series_step(
    series_id: UUID,
    request: SeriesPreviewInput,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[ContentSeriesQueryService, Depends(get_content_series_query_service)],
) -> SeriesPreviewMessage:
    """Render one localized simulator message without persisting it."""
    del current_user
    return await service.preview(series_id, request)
