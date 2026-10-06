"""Coordinator follow-up inbox API schemas."""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import FollowUpPriority, FollowUpStatus, FollowUpType, LanguageCode


class FollowUpResolveOutcome(StrEnum):
    """Client-visible resolution outcomes for the MVP inbox."""

    ATTENDED = "attended"
    REBOOKED = "rebooked"
    NOT_REACHABLE = "not_reachable"


class NamedResource(BaseModel):
    id: UUID
    name: str


class FollowUpDonorList(BaseModel):
    id: UUID
    name: str
    phone: str


class FollowUpAssignee(BaseModel):
    id: UUID
    full_name: str


class LatestReply(BaseModel):
    body: str
    created_at: datetime


class FollowUpListItem(BaseModel):
    id: UUID
    enrollment_id: UUID
    donor: FollowUpDonorList
    campaign: NamedResource
    type: FollowUpType
    status: FollowUpStatus
    priority: FollowUpPriority
    latest_reply: LatestReply | None
    assigned_to: FollowUpAssignee | None
    created_at: datetime
    updated_at: datetime


class FollowUpPage(BaseModel):
    items: list[FollowUpListItem]
    total: int
    page: int
    page_size: int


class FollowUpInboxSummary(BaseModel):
    total: int
    by_type: dict[FollowUpType, int]
    by_status: dict[FollowUpStatus, int]


class FollowUpDonorDetail(FollowUpDonorList):
    language: LanguageCode
    segment: str
    city: str | None
    blood_group: str | None
    last_donation_date: date | None


class FollowUpEnrollment(BaseModel):
    id: UUID
    status: str


class LatestResponse(BaseModel):
    intent: str
    requested_date: date | None
    decline_reason: str | None
    confidence: float | None
    raw_text: str
    created_at: datetime


class FollowUpAppointment(BaseModel):
    center_name: str
    slot_start: datetime


class FollowUpActivityOut(BaseModel):
    id: UUID
    action: str
    note: str | None
    user_name: str | None
    created_at: datetime


class FollowUpDetail(FollowUpListItem):
    donor: FollowUpDonorDetail
    enrollment: FollowUpEnrollment
    latest_response: LatestResponse | None
    appointment: FollowUpAppointment | None
    activities: list[FollowUpActivityOut]


class FollowUpUpdate(BaseModel):
    status: FollowUpStatus | None = None
    assigned_to_id: UUID | None = None
    priority: FollowUpPriority | None = None


class FollowUpNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class FollowUpResolve(BaseModel):
    outcome: FollowUpResolveOutcome
    note: str | None = Field(default=None, max_length=2000)
