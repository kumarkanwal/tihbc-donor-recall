"""Coordinator follow-up item and activity models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    FOLLOW_UP_OUTCOME_DB,
    FOLLOW_UP_PRIORITY_DB,
    FOLLOW_UP_STATUS_DB,
    FOLLOW_UP_TYPE_DB,
    FollowUpOutcome,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)

if TYPE_CHECKING:
    from app.models.campaign import Enrollment
    from app.models.user import User


class FollowUpItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A coordinator task created from an enrollment outcome."""

    __tablename__ = "follow_up_items"
    __table_args__ = (
        Index(
            "uq_follow_up_items_open_enrollment",
            "enrollment_id",
            unique=True,
            postgresql_where=text("status <> 'done'::follow_up_status"),
        ),
    )

    enrollment_id: Mapped[UUID] = mapped_column(
        ForeignKey("enrollments.id"), nullable=False, index=True
    )
    type: Mapped[FollowUpType] = mapped_column(FOLLOW_UP_TYPE_DB, nullable=False)
    status: Mapped[FollowUpStatus] = mapped_column(
        FOLLOW_UP_STATUS_DB,
        nullable=False,
        default=FollowUpStatus.OPEN,
        server_default=text("'open'::follow_up_status"),
    )
    priority: Mapped[FollowUpPriority] = mapped_column(FOLLOW_UP_PRIORITY_DB, nullable=False)
    assigned_to_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    outcome: Mapped[FollowUpOutcome | None] = mapped_column(FOLLOW_UP_OUTCOME_DB)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)

    enrollment: Mapped["Enrollment"] = relationship(back_populates="follow_up_items")
    assigned_to: Mapped["User | None"] = relationship(
        back_populates="assigned_follow_ups", foreign_keys=[assigned_to_id]
    )
    resolved_by: Mapped["User | None"] = relationship(
        back_populates="resolved_follow_ups", foreign_keys=[resolved_by_id]
    )
    activities: Mapped[list["FollowUpActivity"]] = relationship(back_populates="follow_up")


class FollowUpActivity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An auditable action recorded against a follow-up item."""

    __tablename__ = "follow_up_activities"

    follow_up_id: Mapped[UUID] = mapped_column(
        ForeignKey("follow_up_items.id"), nullable=False, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    follow_up: Mapped[FollowUpItem] = relationship(back_populates="activities")
    user: Mapped["User | None"] = relationship(back_populates="follow_up_activities")
