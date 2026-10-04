"""Create the complete Phase 1 database schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENUM_DEFINITIONS = (
    ("user_role", ("admin", "coordinator")),
    ("language_code", ("en", "ur")),
    ("series_kind", ("primary", "secondary")),
    ("series_status", ("draft", "active", "archived")),
    ("message_category", ("utility", "marketing")),
    ("media_type", ("none", "image", "video")),
    ("campaign_status", ("draft", "scheduled", "running", "paused", "completed")),
    (
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
    ("message_direction", ("outbound", "inbound")),
    ("message_kind", ("template", "text", "interactive", "button_reply")),
    ("message_status", ("queued", "sent", "delivered", "read", "failed")),
    ("response_intent", ("confirm", "reschedule", "decline", "question", "unknown")),
    ("response_source", ("button", "agent")),
    (
        "decline_reason",
        ("travelling", "health", "recently_donated", "not_interested", "other"),
    ),
    ("follow_up_type", ("confirmed", "reschedule", "declined", "needs_call")),
    ("follow_up_status", ("open", "in_progress", "done")),
    ("follow_up_priority", ("normal", "high")),
    (
        "follow_up_outcome",
        ("attended", "rebooked", "not_reachable", "declined", "other"),
    ),
)


def _id_column() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def _create_indexes(table_name: str, *column_names: str) -> None:
    for column_name in column_names:
        op.create_index(f"ix_{table_name}_{column_name}", table_name, [column_name])


def upgrade() -> None:
    """Create enums, tables, constraints, and indexes."""
    bind = op.get_bind()
    for name, values in ENUM_DEFINITIONS:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=False)

    op.create_table(
        "users",
        _id_column(),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", _enum("user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "segments",
        _id_column(),
        sa.Column("key", sa.String(40), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("key", name="uq_segments_key"),
    )
    op.create_table(
        "tags",
        _id_column(),
        sa.Column("name", sa.String(40), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("name", name="uq_tags_name"),
    )
    op.create_table(
        "appointment_slots",
        _id_column(),
        sa.Column("center_name", sa.String(120), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("booked_count", sa.Integer(), server_default="0", nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "booked_count <= capacity", name="ck_appointment_slots_booked_count_within_capacity"
        ),
    )
    op.create_index("ix_appointment_slots_starts_at", "appointment_slots", ["starts_at"])
    op.create_table(
        "demo_clock",
        sa.Column("id", sa.SmallInteger(), server_default="1", primary_key=True),
        sa.Column("offset_seconds", sa.BigInteger(), server_default="0", nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("id = 1", name="ck_demo_clock_singleton_id"),
    )
    op.create_table(
        "donor_batches",
        _id_column(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("invalid_rows", sa.Integer(), nullable=False),
        sa.Column("validation_report", postgresql.JSONB(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
    )
    _create_indexes("donor_batches", "uploaded_by_id")
    op.create_table(
        "donors",
        _id_column(),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("phone_e164", sa.String(16), nullable=False),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", _enum("language_code"), nullable=False),
        sa.Column("city", sa.String(80)),
        sa.Column("blood_group", sa.String(3)),
        sa.Column("last_donation_date", sa.Date()),
        sa.Column("sim_reachable", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sim_read_receipts", sa.Boolean(), server_default=sa.true(), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["batch_id"], ["donor_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["segment_id"], ["segments.id"]),
        sa.UniqueConstraint("batch_id", "phone_e164", name="uq_donors_batch_id_phone_e164"),
    )
    _create_indexes("donors", "batch_id", "segment_id", "phone_e164")
    op.create_table(
        "content_series",
        _id_column(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("kind", _enum("series_kind"), nullable=False),
        sa.Column("status", _enum("series_status"), server_default="draft", nullable=False),
        sa.Column("languages", postgresql.ARRAY(_enum("language_code")), nullable=False),
        sa.Column("response_window_hours", sa.Integer(), server_default="48", nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
    )
    _create_indexes("content_series", "created_by_id")
    op.create_table(
        "series_tags",
        sa.Column("series_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.ForeignKeyConstraint(["series_id"], ["content_series.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
    )
    _create_indexes("series_tags", "series_id", "tag_id")
    op.create_table(
        "series_steps",
        _id_column(),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("delay_days", sa.Integer(), nullable=False),
        sa.Column("category", _enum("message_category"), nullable=False),
        sa.Column("media_type", _enum("media_type"), server_default="none", nullable=False),
        sa.Column("media_url", sa.String(500)),
        sa.Column("buttons", postgresql.JSONB(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("step_order >= 1", name="ck_series_steps_step_order_positive"),
        sa.ForeignKeyConstraint(["series_id"], ["content_series.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("series_id", "step_order", name="uq_series_steps_series_id_step_order"),
    )
    _create_indexes("series_steps", "series_id")
    op.create_table(
        "series_step_contents",
        _id_column(),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", _enum("language_code"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "char_length(body) <= 1024", name="ck_series_step_contents_body_max_length"
        ),
        sa.ForeignKeyConstraint(["step_id"], ["series_steps.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("step_id", "language", name="uq_series_step_contents_step_id_language"),
    )
    _create_indexes("series_step_contents", "step_id")
    _create_campaign_tables()
    _create_messaging_tables()
    _create_follow_up_tables()


def _create_campaign_tables() -> None:
    op.create_table(
        "campaigns",
        _id_column(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_series_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("secondary_series_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", _enum("campaign_status"), server_default="draft", nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("launched_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["batch_id"], ["donor_batches.id"]),
        sa.ForeignKeyConstraint(["primary_series_id"], ["content_series.id"]),
        sa.ForeignKeyConstraint(["secondary_series_id"], ["content_series.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
    )
    _create_indexes(
        "campaigns", "batch_id", "primary_series_id", "secondary_series_id", "created_by_id"
    )
    op.create_table(
        "enrollments",
        _id_column(),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("donor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", _enum("enrollment_status"), nullable=False),
        sa.Column("current_series_kind", _enum("series_kind")),
        sa.Column("current_step_order", sa.Integer()),
        sa.Column("next_action_at", sa.DateTime(timezone=True)),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.Column("appointment_slot_id", postgresql.UUID(as_uuid=True)),
        sa.Column("decline_reason", _enum("decline_reason")),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["donor_id"], ["donors.id"]),
        sa.ForeignKeyConstraint(["appointment_slot_id"], ["appointment_slots.id"]),
        sa.UniqueConstraint("campaign_id", "donor_id", name="uq_enrollments_campaign_id_donor_id"),
    )
    _create_indexes(
        "enrollments", "campaign_id", "donor_id", "appointment_slot_id", "status", "next_action_at"
    )


def _create_messaging_tables() -> None:
    op.create_table(
        "messages",
        _id_column(),
        sa.Column("donor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True)),
        sa.Column("step_id", postgresql.UUID(as_uuid=True)),
        sa.Column("direction", _enum("message_direction"), nullable=False),
        sa.Column("kind", _enum("message_kind"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("media_type", _enum("media_type"), nullable=False),
        sa.Column("media_url", sa.String(500)),
        sa.Column("buttons", postgresql.JSONB()),
        sa.Column("reply_to_message_id", postgresql.UUID(as_uuid=True)),
        sa.Column("button_id", sa.String(40)),
        sa.Column("status", _enum("message_status"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("failed_reason", sa.String(120)),
        sa.Column("provider_message_id", sa.String(120)),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["donor_id"], ["donors.id"]),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["step_id"], ["series_steps.id"]),
        sa.ForeignKeyConstraint(["reply_to_message_id"], ["messages.id"]),
    )
    _create_indexes("messages", "donor_id", "enrollment_id", "step_id", "reply_to_message_id")
    op.create_index("ix_messages_donor_id_created_at", "messages", ["donor_id", "created_at"])
    op.create_index("ix_messages_status_scheduled_at", "messages", ["status", "scheduled_at"])
    op.create_table(
        "donor_responses",
        _id_column(),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent", _enum("response_intent"), nullable=False),
        sa.Column("source", _enum("response_source"), nullable=False),
        sa.Column("detected_language", sa.String(8), nullable=False),
        sa.Column("requested_date", sa.Date()),
        sa.Column("decline_reason", _enum("decline_reason")),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False),
        sa.Column("trace_id", sa.String(120)),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
    )
    _create_indexes("donor_responses", "enrollment_id", "message_id")


def _create_follow_up_tables() -> None:
    op.create_table(
        "follow_up_items",
        _id_column(),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", _enum("follow_up_type"), nullable=False),
        sa.Column("status", _enum("follow_up_status"), server_default="open", nullable=False),
        sa.Column("priority", _enum("follow_up_priority"), nullable=False),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True)),
        sa.Column("outcome", _enum("follow_up_outcome")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True)),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"]),
    )
    _create_indexes("follow_up_items", "enrollment_id", "assigned_to_id", "resolved_by_id")
    op.create_index(
        "uq_follow_up_items_open_enrollment",
        "follow_up_items",
        ["enrollment_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'done'::follow_up_status"),
    )
    op.create_table(
        "follow_up_activities",
        _id_column(),
        sa.Column("follow_up_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("note", sa.Text()),
        *_timestamp_columns(),
        sa.ForeignKeyConstraint(["follow_up_id"], ["follow_up_items.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    _create_indexes("follow_up_activities", "follow_up_id", "user_id")


def downgrade() -> None:
    """Drop the Phase 1 schema and its PostgreSQL enums."""
    for table_name in (
        "follow_up_activities",
        "follow_up_items",
        "donor_responses",
        "messages",
        "enrollments",
        "campaigns",
        "series_step_contents",
        "series_steps",
        "series_tags",
        "content_series",
        "donors",
        "donor_batches",
        "demo_clock",
        "appointment_slots",
        "tags",
        "segments",
        "users",
    ):
        op.drop_table(table_name)

    bind = op.get_bind()
    for name, values in reversed(ENUM_DEFINITIONS):
        postgresql.ENUM(*values, name=name).drop(bind, checkfirst=False)
