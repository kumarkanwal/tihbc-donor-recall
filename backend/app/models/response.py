"""Classified donor response model."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    DECLINE_REASON_DB,
    RESPONSE_INTENT_DB,
    RESPONSE_SOURCE_DB,
    DeclineReason,
    ResponseIntent,
    ResponseSource,
)

if TYPE_CHECKING:
    from app.models.campaign import Enrollment
    from app.models.message import Message


class DonorResponse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A structured classification of one inbound donor message."""

    __tablename__ = "donor_responses"

    enrollment_id: Mapped[UUID] = mapped_column(
        ForeignKey("enrollments.id"), nullable=False, index=True
    )
    message_id: Mapped[UUID] = mapped_column(ForeignKey("messages.id"), nullable=False, index=True)
    intent: Mapped[ResponseIntent] = mapped_column(RESPONSE_INTENT_DB, nullable=False)
    source: Mapped[ResponseSource] = mapped_column(RESPONSE_SOURCE_DB, nullable=False)
    detected_language: Mapped[str] = mapped_column(String(8), nullable=False)
    requested_date: Mapped[date | None] = mapped_column(Date)
    decline_reason: Mapped[DeclineReason | None] = mapped_column(DECLINE_REASON_DB)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(120))

    enrollment: Mapped["Enrollment"] = relationship(back_populates="responses")
    message: Mapped["Message"] = relationship(back_populates="donor_response")
