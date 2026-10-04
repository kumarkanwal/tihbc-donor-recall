"""Tests for database enum definitions."""

import pytest
from sqlalchemy import Enum as SQLAlchemyEnum

from app.models import enums

ENUM_CASES = (
    (enums.USER_ROLE_DB, "user_role", ("admin", "coordinator")),
    (enums.LANGUAGE_CODE_DB, "language_code", ("en", "ur")),
    (enums.SERIES_KIND_DB, "series_kind", ("primary", "secondary")),
    (enums.SERIES_STATUS_DB, "series_status", ("draft", "active", "archived")),
    (enums.MESSAGE_CATEGORY_DB, "message_category", ("utility", "marketing")),
    (enums.MEDIA_TYPE_DB, "media_type", ("none", "image", "video")),
    (
        enums.CAMPAIGN_STATUS_DB,
        "campaign_status",
        ("draft", "scheduled", "running", "paused", "completed"),
    ),
    (
        enums.ENROLLMENT_STATUS_DB,
        "enrollment_status",
        (
            "pending",
            "in_primary",
            "in_secondary",
            "escalated",
            "confirmed",
            "reschedule_requested",
            "rescheduled",
            "declined",
            "invalid_number",
            "undeliverable",
        ),
    ),
    (enums.MESSAGE_DIRECTION_DB, "message_direction", ("outbound", "inbound")),
    (
        enums.MESSAGE_KIND_DB,
        "message_kind",
        ("template", "text", "interactive", "button_reply"),
    ),
    (
        enums.MESSAGE_STATUS_DB,
        "message_status",
        ("queued", "sent", "delivered", "read", "failed"),
    ),
    (
        enums.RESPONSE_INTENT_DB,
        "response_intent",
        ("confirm", "reschedule", "decline", "question", "unknown"),
    ),
    (enums.RESPONSE_SOURCE_DB, "response_source", ("button", "agent")),
    (
        enums.DECLINE_REASON_DB,
        "decline_reason",
        ("travelling", "health", "recently_donated", "not_interested", "other"),
    ),
    (
        enums.FOLLOW_UP_TYPE_DB,
        "follow_up_type",
        ("confirmed", "reschedule", "declined", "needs_call"),
    ),
    (enums.FOLLOW_UP_STATUS_DB, "follow_up_status", ("open", "in_progress", "done")),
    (enums.FOLLOW_UP_PRIORITY_DB, "follow_up_priority", ("normal", "high")),
    (
        enums.FOLLOW_UP_OUTCOME_DB,
        "follow_up_outcome",
        ("attended", "rebooked", "not_reachable", "declined", "other"),
    ),
)


@pytest.mark.parametrize(("database_type", "name", "values"), ENUM_CASES)
def test_database_enum_matches_spec(
    database_type: SQLAlchemyEnum, name: str, values: tuple[str, ...]
) -> None:
    assert database_type.name == name
    assert tuple(database_type.enums) == values
    assert database_type.native_enum is True
