"""Canonical domain-event names, public payloads, and wire envelope."""

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import (
    CampaignStatus,
    EnrollmentStatus,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    SeriesKind,
)
from app.schemas.campaign import FollowUpSummary
from app.schemas.demo import DemoClockOut

EVENT_CHANNEL = "tihbc:events"
METRICS_DEBOUNCE_SECONDS = 2.0


class EventType(StrEnum):
    """Event names in docs/websocket.md."""

    MESSAGE_CREATED = "message.created"
    MESSAGE_STATUS_UPDATED = "message.status_updated"
    SIMULATOR_TYPING = "simulator.typing"
    ENROLLMENT_UPDATED = "enrollment.updated"
    FOLLOWUP_CREATED = "followup.created"
    FOLLOWUP_UPDATED = "followup.updated"
    CAMPAIGN_UPDATED = "campaign.updated"
    METRICS_UPDATED = "metrics.updated"
    CLOCK_UPDATED = "clock.updated"


class MessageButton(BaseModel):
    """A localized public button."""

    id: str
    label: str


class MessagePayload(BaseModel):
    """Simulator REST message representation without internal recipient data."""

    id: UUID
    donor_id: UUID
    direction: MessageDirection
    kind: MessageKind
    body: str
    media_type: MediaType
    media_url: str | None
    buttons: list[MessageButton] | None
    button_id: str | None
    reply_to_message_id: UUID | None
    status: MessageStatus
    scheduled_at: datetime
    created_at: datetime
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None


class MessageStatusPayload(BaseModel):
    """Public delivery update."""

    id: UUID
    donor_id: UUID
    status: MessageStatus
    delivered_at: datetime | None
    read_at: datetime | None
    failed_reason: str | None


class TypingPayload(BaseModel):
    """Simulator typing state."""

    donor_id: UUID
    is_typing: bool


class EnrollmentPayload(BaseModel):
    """Enrollment progress shared with both staff roles."""

    id: UUID
    campaign_id: UUID
    donor_id: UUID
    status: EnrollmentStatus
    current_series_kind: SeriesKind | None
    current_step_order: int | None


class FollowUpPayload(FollowUpSummary):
    """Follow-up list fields produced by escalation."""

    enrollment_id: UUID


class CampaignPayload(BaseModel):
    """Campaign status and enrollment counts."""

    id: UUID
    status: CampaignStatus
    counts: dict[EnrollmentStatus, int]


class MetricsPayload(BaseModel):
    """Campaign-specific or global metrics invalidation."""

    campaign_id: UUID | None


PAYLOAD_MODELS: dict[EventType, type[BaseModel]] = {
    EventType.MESSAGE_CREATED: MessagePayload,
    EventType.MESSAGE_STATUS_UPDATED: MessageStatusPayload,
    EventType.SIMULATOR_TYPING: TypingPayload,
    EventType.ENROLLMENT_UPDATED: EnrollmentPayload,
    EventType.FOLLOWUP_CREATED: FollowUpPayload,
    EventType.FOLLOWUP_UPDATED: FollowUpPayload,
    EventType.CAMPAIGN_UPDATED: CampaignPayload,
    EventType.METRICS_UPDATED: MetricsPayload,
    EventType.CLOCK_UPDATED: DemoClockOut,
}


class EventEnvelope(BaseModel):
    """Exact public wire envelope."""

    type: EventType
    payload: dict[str, object]
    ts: datetime

    def public(self) -> "EventEnvelope":
        """Discard internal fields at either transport boundary."""
        return self.model_copy(update={"payload": public_payload(self.type, self.payload)})


def public_payload(event_type: EventType, payload: Mapping[str, object]) -> dict[str, object]:
    """Allow only documented fields, shared by both authorized staff roles."""
    return PAYLOAD_MODELS[event_type].model_validate(dict(payload)).model_dump(mode="json")
