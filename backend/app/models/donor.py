"""Donor, segment, and upload batch models."""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, UniqueConstraint, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LANGUAGE_CODE_DB, LanguageCode

if TYPE_CHECKING:
    from app.models.campaign import Campaign, Enrollment
    from app.models.message import Message
    from app.models.user import User


class Segment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable donor grouping label."""

    __tablename__ = "segments"

    key: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)

    donors: Mapped[list["Donor"]] = relationship(back_populates="segment")


class DonorBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A validated donor upload and its stored validation report."""

    __tablename__ = "donor_batches"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_report: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)

    uploaded_by: Mapped["User"] = relationship(back_populates="uploaded_batches")
    donors: Mapped[list["Donor"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan", passive_deletes=True
    )
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="batch")


class Donor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A donor imported as part of one donor batch."""

    __tablename__ = "donors"
    __table_args__ = (
        UniqueConstraint("batch_id", "phone_e164"),
        Index("ix_donors_phone_e164", "phone_e164"),
    )

    batch_id: Mapped[UUID] = mapped_column(
        ForeignKey("donor_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(16), nullable=False)
    segment_id: Mapped[UUID] = mapped_column(ForeignKey("segments.id"), nullable=False, index=True)
    language: Mapped[LanguageCode] = mapped_column(LANGUAGE_CODE_DB, nullable=False)
    city: Mapped[str | None] = mapped_column(String(80))
    blood_group: Mapped[str | None] = mapped_column(String(3))
    last_donation_date: Mapped[date | None] = mapped_column(Date)
    sim_reachable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    sim_read_receipts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    batch: Mapped[DonorBatch] = relationship(back_populates="donors")
    segment: Mapped[Segment] = relationship(back_populates="donors")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="donor")
    messages: Mapped[list["Message"]] = relationship(back_populates="donor")
