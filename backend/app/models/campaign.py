"""Campaign, enrollment, and appointment-slot models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    CAMPAIGN_STATUS_DB,
    DECLINE_REASON_DB,
    ENROLLMENT_STATUS_DB,
    SERIES_KIND_DB,
    CampaignStatus,
    DeclineReason,
    EnrollmentStatus,
    SeriesKind,
)

if TYPE_CHECKING:
    from app.models.donor import Donor, DonorBatch
    from app.models.follow_up import FollowUpItem
    from app.models.message import Message
    from app.models.response import DonorResponse
    from app.models.series import ContentSeries
    from app.models.user import User


class AppointmentSlot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A capacity-limited appointment time at one center."""

    __tablename__ = "appointment_slots"
    __table_args__ = (
        CheckConstraint("booked_count <= capacity", name="booked_count_within_capacity"),
        Index("ix_appointment_slots_starts_at", "starts_at"),
    )

    center_name: Mapped[str] = mapped_column(String(120), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    booked_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="appointment_slot")


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A batch assigned to primary and secondary content series."""

    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("donor_batches.id"), nullable=False, index=True
    )
    primary_series_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_series.id"), nullable=False, index=True
    )
    secondary_series_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_series.id"), nullable=False, index=True
    )
    status: Mapped[CampaignStatus] = mapped_column(
        CAMPAIGN_STATUS_DB,
        nullable=False,
        default=CampaignStatus.DRAFT,
        server_default=text("'draft'::campaign_status"),
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    batch: Mapped["DonorBatch"] = relationship(back_populates="campaigns")
    primary_series: Mapped["ContentSeries"] = relationship(
        back_populates="primary_campaigns", foreign_keys=[primary_series_id]
    )
    secondary_series: Mapped["ContentSeries"] = relationship(
        back_populates="secondary_campaigns", foreign_keys=[secondary_series_id]
    )
    created_by: Mapped["User"] = relationship(back_populates="created_campaigns")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="campaign")


class Enrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One donor's progress through one campaign."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("campaign_id", "donor_id"),
        Index("ix_enrollments_status", "status"),
        Index("ix_enrollments_next_action_at", "next_action_at"),
    )

    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id"), nullable=False, index=True
    )
    donor_id: Mapped[UUID] = mapped_column(ForeignKey("donors.id"), nullable=False, index=True)
    status: Mapped[EnrollmentStatus] = mapped_column(ENROLLMENT_STATUS_DB, nullable=False)
    current_series_kind: Mapped[SeriesKind | None] = mapped_column(SERIES_KIND_DB)
    current_step_order: Mapped[int | None] = mapped_column(Integer)
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    appointment_slot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("appointment_slots.id"), index=True
    )
    decline_reason: Mapped[DeclineReason | None] = mapped_column(DECLINE_REASON_DB)

    campaign: Mapped[Campaign] = relationship(back_populates="enrollments")
    donor: Mapped["Donor"] = relationship(back_populates="enrollments")
    appointment_slot: Mapped[AppointmentSlot | None] = relationship(back_populates="enrollments")
    messages: Mapped[list["Message"]] = relationship(back_populates="enrollment")
    responses: Mapped[list["DonorResponse"]] = relationship(back_populates="enrollment")
    follow_up_items: Mapped[list["FollowUpItem"]] = relationship(back_populates="enrollment")
