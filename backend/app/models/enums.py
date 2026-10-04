"""Domain enums and their PostgreSQL type definitions."""

from enum import StrEnum

from sqlalchemy import Enum as SQLAlchemyEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    COORDINATOR = "coordinator"


class LanguageCode(StrEnum):
    EN = "en"
    UR = "ur"


class SeriesKind(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class SeriesStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageCategory(StrEnum):
    UTILITY = "utility"
    MARKETING = "marketing"


class MediaType(StrEnum):
    NONE = "none"
    IMAGE = "image"
    VIDEO = "video"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class EnrollmentStatus(StrEnum):
    PENDING = "pending"
    IN_PRIMARY = "in_primary"
    IN_SECONDARY = "in_secondary"
    ESCALATED = "escalated"
    CONFIRMED = "confirmed"
    RESCHEDULE_REQUESTED = "reschedule_requested"
    RESCHEDULED = "rescheduled"
    DECLINED = "declined"
    INVALID_NUMBER = "invalid_number"
    UNDELIVERABLE = "undeliverable"


class MessageDirection(StrEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class MessageKind(StrEnum):
    TEMPLATE = "template"
    TEXT = "text"
    INTERACTIVE = "interactive"
    BUTTON_REPLY = "button_reply"


class MessageStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ResponseIntent(StrEnum):
    CONFIRM = "confirm"
    RESCHEDULE = "reschedule"
    DECLINE = "decline"
    QUESTION = "question"
    UNKNOWN = "unknown"


class ResponseSource(StrEnum):
    BUTTON = "button"
    AGENT = "agent"


class DeclineReason(StrEnum):
    TRAVELLING = "travelling"
    HEALTH = "health"
    RECENTLY_DONATED = "recently_donated"
    NOT_INTERESTED = "not_interested"
    OTHER = "other"


class FollowUpType(StrEnum):
    CONFIRMED = "confirmed"
    RESCHEDULE = "reschedule"
    DECLINED = "declined"
    NEEDS_CALL = "needs_call"


class FollowUpStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class FollowUpPriority(StrEnum):
    NORMAL = "normal"
    HIGH = "high"


class FollowUpOutcome(StrEnum):
    ATTENDED = "attended"
    REBOOKED = "rebooked"
    NOT_REACHABLE = "not_reachable"
    DECLINED = "declined"
    OTHER = "other"


def _enum_values[EnumValue: StrEnum](enum_class: type[EnumValue]) -> list[str]:
    return [member.value for member in enum_class]


def database_enum[EnumValue: StrEnum](enum_class: type[EnumValue], name: str) -> SQLAlchemyEnum:
    """Map a string enum to a named native PostgreSQL enum."""
    return SQLAlchemyEnum(
        enum_class,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=_enum_values,
    )


USER_ROLE_DB = database_enum(UserRole, "user_role")
LANGUAGE_CODE_DB = database_enum(LanguageCode, "language_code")
SERIES_KIND_DB = database_enum(SeriesKind, "series_kind")
SERIES_STATUS_DB = database_enum(SeriesStatus, "series_status")
MESSAGE_CATEGORY_DB = database_enum(MessageCategory, "message_category")
MEDIA_TYPE_DB = database_enum(MediaType, "media_type")
CAMPAIGN_STATUS_DB = database_enum(CampaignStatus, "campaign_status")
ENROLLMENT_STATUS_DB = database_enum(EnrollmentStatus, "enrollment_status")
MESSAGE_DIRECTION_DB = database_enum(MessageDirection, "message_direction")
MESSAGE_KIND_DB = database_enum(MessageKind, "message_kind")
MESSAGE_STATUS_DB = database_enum(MessageStatus, "message_status")
RESPONSE_INTENT_DB = database_enum(ResponseIntent, "response_intent")
RESPONSE_SOURCE_DB = database_enum(ResponseSource, "response_source")
DECLINE_REASON_DB = database_enum(DeclineReason, "decline_reason")
FOLLOW_UP_TYPE_DB = database_enum(FollowUpType, "follow_up_type")
FOLLOW_UP_STATUS_DB = database_enum(FollowUpStatus, "follow_up_status")
FOLLOW_UP_PRIORITY_DB = database_enum(FollowUpPriority, "follow_up_priority")
FOLLOW_UP_OUTCOME_DB = database_enum(FollowUpOutcome, "follow_up_outcome")
