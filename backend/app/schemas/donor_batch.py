"""Schemas for donor batch preview, import, and browsing."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LanguageCode


class ValidationIssue(BaseModel):
    """One row-level upload validation error."""

    row: int
    field: str
    value: str
    reason: str


class ExistingPhoneWarning(BaseModel):
    """A valid phone that also appears in an earlier batch."""

    row: int
    phone: str
    existing_batch_name: str


class SegmentBreakdown(BaseModel):
    """Preview or batch count for one segment."""

    segment: str
    count: int


class LanguageBreakdown(BaseModel):
    """Preview or batch count for one donor language."""

    language: LanguageCode
    count: int


class DonorPreviewRow(BaseModel):
    """One normalized valid donor shown during review."""

    row: int
    name: str
    phone: str
    segment: str
    language: LanguageCode
    city: str | None = None
    blood_group: str | None = None
    last_donation_date: date | None = None


class StoredDonorRow(DonorPreviewRow):
    """Normalized donor data retained for transactional import."""

    segment_id: UUID


class StoredBatchPreview(BaseModel):
    """Complete validated preview retained temporarily in Redis."""

    original_filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    donors: list[StoredDonorRow]
    segment_breakdown: list[SegmentBreakdown]
    language_breakdown: list[LanguageBreakdown]
    errors: list[ValidationIssue]
    warnings: list[ExistingPhoneWarning]
    expires_at: datetime


class BatchPreview(BaseModel):
    """Upload validation result returned to the review screen."""

    preview_token: str
    original_filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    segment_breakdown: list[SegmentBreakdown]
    language_breakdown: list[LanguageBreakdown]
    sample_valid_rows: list[DonorPreviewRow]
    errors: list[ValidationIssue]
    warnings: list[ExistingPhoneWarning]


class BatchImportRequest(BaseModel):
    """Request to persist the valid rows from one preview."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    preview_token: str = Field(min_length=1, max_length=255)


class UploadedBySummary(BaseModel):
    """Minimal uploader identity displayed with a batch."""

    id: UUID
    full_name: str


class DonorBatchOut(BaseModel):
    """Summary of one imported donor batch."""

    id: UUID
    name: str
    original_filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    uploaded_by: UploadedBySummary
    created_at: datetime
    campaign_count: int


class DonorBatchPage(BaseModel):
    """Paginated donor batch summaries."""

    items: list[DonorBatchOut]
    total: int
    page: int
    page_size: int


class DonorBatchDetail(DonorBatchOut):
    """Batch summary with segment and language counts."""

    segment_breakdown: list[SegmentBreakdown]
    language_breakdown: list[LanguageBreakdown]


class DonorOut(BaseModel):
    """Masked donor row for staff batch browsing."""

    id: UUID
    full_name: str
    phone_e164: str
    segment: str
    language: LanguageCode
    city: str | None
    blood_group: str | None
    last_donation_date: date | None
    created_at: datetime


class DonorPage(BaseModel):
    """Paginated donors within one batch."""

    items: list[DonorOut]
    total: int
    page: int
    page_size: int
