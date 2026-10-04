"""Campaign lifecycle and enrollment API schemas."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    CampaignStatus,
    DeclineReason,
    EnrollmentStatus,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
    LanguageCode,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    ResponseIntent,
    ResponseSource,
    SeriesKind,
)
from app.schemas.donor_batch import UploadedBySummary


class CampaignCreate(BaseModel):
    """Create one draft campaign."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    batch_id: UUID
    primary_series_id: UUID
    secondary_series_id: UUID
    start_at: datetime

    @field_validator("start_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        """Require an aware timestamp and normalize it to UTC."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start_at must include a timezone")
        return value.astimezone(UTC)


class CampaignUpdate(BaseModel):
    """Update selected draft campaign settings."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    batch_id: UUID | None = None
    primary_series_id: UUID | None = None
    secondary_series_id: UUID | None = None
    start_at: datetime | None = None

    @field_validator("start_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime | None) -> datetime | None:
        """Require an aware timestamp and normalize it to UTC."""
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start_at must include a timezone")
        return value.astimezone(UTC)


class NamedResourceSummary(BaseModel):
    """Identifier and display name for a related resource."""

    id: UUID
    name: str


class CampaignOut(BaseModel):
    """Campaign list representation."""

    id: UUID
    name: str
    batch: NamedResourceSummary
    primary_series: NamedResourceSummary
    secondary_series: NamedResourceSummary
    status: CampaignStatus
    start_at: datetime
    launched_at: datetime | None
    completed_at: datetime | None
    enrollment_count: int
    responded_count: int
    response_rate: float
    created_by: UploadedBySummary
    created_at: datetime
    updated_at: datetime


class CampaignDetail(CampaignOut):
    """Campaign summary with every enrollment-status count."""

    enrollment_counts: dict[EnrollmentStatus, int]


class CampaignPage(BaseModel):
    """Paginated campaign summaries."""

    items: list[CampaignOut]
    total: int
    page: int
    page_size: int


class CampaignLaunchProblem(BaseModel):
    """One actionable campaign launch problem."""

    field: str
    reason: str


class EnrollmentDonorOut(BaseModel):
    """Donor information returned with an enrollment."""

    id: UUID
    full_name: str
    phone_e164: str
    segment: str
    language: LanguageCode
    city: str | None
    blood_group: str | None
    last_donation_date: date | None


class EnrollmentOut(BaseModel):
    """Enrollment list representation."""

    id: UUID
    campaign_id: UUID
    donor: EnrollmentDonorOut
    status: EnrollmentStatus
    current_series_kind: SeriesKind | None
    current_step_order: int | None
    next_action_at: datetime | None
    responded_at: datetime | None
    decline_reason: DeclineReason | None
    created_at: datetime
    updated_at: datetime


class EnrollmentPage(BaseModel):
    """Paginated campaign enrollments."""

    items: list[EnrollmentOut]
    total: int
    page: int
    page_size: int


class MessageTimelineEntry(BaseModel):
    """Message data embedded in an enrollment timeline."""

    direction: MessageDirection
    kind: MessageKind
    body: str
    media_type: MediaType
    media_url: str | None
    status: MessageStatus
    scheduled_at: datetime
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None


class ResponseTimelineEntry(BaseModel):
    """Classified response data embedded in an enrollment timeline."""

    intent: ResponseIntent
    source: ResponseSource
    detected_language: str
    requested_date: date | None
    decline_reason: DeclineReason | None
    confidence: Decimal


class EnrollmentTimelineItem(BaseModel):
    """Chronological message or response event."""

    id: UUID
    type: Literal["message", "response"]
    created_at: datetime
    message: MessageTimelineEntry | None = None
    response: ResponseTimelineEntry | None = None


class FollowUpSummary(BaseModel):
    """Current or most recent coordinator follow-up."""

    id: UUID
    type: FollowUpType
    status: FollowUpStatus
    priority: FollowUpPriority
    assigned_to_id: UUID | None
    created_at: datetime
    updated_at: datetime


class AppointmentSlotSummary(BaseModel):
    """Booked appointment associated with an enrollment."""

    id: UUID
    center_name: str
    starts_at: datetime


class EnrollmentDetail(EnrollmentOut):
    """Enrollment with full donor data and related activity."""

    campaign: NamedResourceSummary
    timeline: list[EnrollmentTimelineItem]
    follow_up: FollowUpSummary | None
    appointment: AppointmentSlotSummary | None
