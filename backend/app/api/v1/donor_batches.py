"""Donor batch upload and browsing API routes."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.api.deps import (
    get_batch_upload_service,
    get_donor_batch_query_service,
    require_role,
)
from app.core.config import Settings, get_settings
from app.models.enums import LanguageCode, UserRole
from app.schemas.donor_batch import (
    BatchImportRequest,
    BatchPreview,
    DonorBatchDetail,
    DonorBatchOut,
    DonorBatchPage,
    DonorPage,
    ValidationIssue,
)
from app.schemas.user import UserOut
from app.services.batch_upload.query_service import DonorBatchQueryService
from app.services.batch_upload.sample_file import SAMPLE_FILENAME, generate_sample_csv
from app.services.batch_upload.service import BatchUploadService

router = APIRouter(prefix="/donor-batches", tags=["Donor Batches"])
admin_access = require_role(UserRole.ADMIN)
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)
MAX_READ_EXTRA_BYTES = 1


@router.get(
    "/sample-file",
    response_model=None,
    response_class=Response,
    summary="Download a donor batch sample CSV",
)
async def download_sample_file(
    current_user: Annotated[UserOut, Depends(admin_access)],
) -> Response:
    """Return a generated CSV with valid columns and example rows."""
    del current_user
    return Response(
        content=generate_sample_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{SAMPLE_FILENAME}"'},
    )


@router.post(
    "/preview",
    response_model=BatchPreview,
    summary="Preview and validate a donor batch upload",
)
async def preview_batch(
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[BatchUploadService, Depends(get_batch_upload_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File(description="CSV or XLSX donor file")],
) -> BatchPreview:
    """Validate an upload without persisting a donor batch."""
    del current_user
    max_bytes = settings.upload_max_mb * 1024 * 1024
    content = await file.read(max_bytes + MAX_READ_EXTRA_BYTES)
    return await service.preview(file.filename or "", content)


@router.post(
    "",
    response_model=DonorBatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Import a validated donor batch",
)
async def import_batch(
    request: BatchImportRequest,
    current_user: Annotated[UserOut, Depends(admin_access)],
    service: Annotated[BatchUploadService, Depends(get_batch_upload_service)],
) -> DonorBatchOut:
    """Persist only valid donors from a live preview token."""
    return await service.import_batch(request, current_user)


@router.get(
    "",
    response_model=DonorBatchPage,
    summary="List donor batches",
)
async def list_batches(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[DonorBatchQueryService, Depends(get_donor_batch_query_service)],
    search: Annotated[str | None, Query(max_length=255)] = None,
    sort: Annotated[Literal["created_at", "-created_at", "name", "-name"], Query()] = "-created_at",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DonorBatchPage:
    """Return searchable and sortable donor batch summaries."""
    del current_user
    return await service.list_batches(
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{batch_id}",
    response_model=DonorBatchDetail,
    summary="Get donor batch details",
)
async def get_batch(
    batch_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[DonorBatchQueryService, Depends(get_donor_batch_query_service)],
) -> DonorBatchDetail:
    """Return one donor batch with breakdowns."""
    del current_user
    return await service.get_batch(batch_id)


@router.get(
    "/{batch_id}/donors",
    response_model=DonorPage,
    summary="List donors in a batch",
)
async def list_batch_donors(
    batch_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[DonorBatchQueryService, Depends(get_donor_batch_query_service)],
    segment: Annotated[str | None, Query(max_length=40)] = None,
    language: Annotated[LanguageCode | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    sort: Annotated[
        Literal["created_at", "-created_at", "full_name", "-full_name"], Query()
    ] = "full_name",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DonorPage:
    """Return filtered donors with masked phone numbers."""
    del current_user
    return await service.list_donors(
        batch_id,
        segment=segment,
        language=language,
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{batch_id}/validation-report",
    response_model=list[ValidationIssue],
    summary="Get a donor batch validation report",
)
async def get_validation_report(
    batch_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[DonorBatchQueryService, Depends(get_donor_batch_query_service)],
) -> list[ValidationIssue]:
    """Return persisted invalid-row details for a donor batch."""
    del current_user
    return await service.validation_report(batch_id)
