"""WebSocket-compatible domain event names."""

from enum import StrEnum


class EventType(StrEnum):
    """Event names defined by the shared WebSocket contract."""

    MESSAGE_CREATED = "message.created"
    MESSAGE_STATUS_UPDATED = "message.status_updated"
    SIMULATOR_TYPING = "simulator.typing"
    ENROLLMENT_UPDATED = "enrollment.updated"
    FOLLOWUP_CREATED = "followup.created"
    FOLLOWUP_UPDATED = "followup.updated"
    CAMPAIGN_UPDATED = "campaign.updated"
    METRICS_UPDATED = "metrics.updated"
    CLOCK_UPDATED = "clock.updated"
