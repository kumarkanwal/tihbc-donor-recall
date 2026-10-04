"""Inbound and outbound simulator message model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    MEDIA_TYPE_DB,
    MESSAGE_DIRECTION_DB,
    MESSAGE_KIND_DB,
    MESSAGE_STATUS_DB,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
)

if TYPE_CHECKING:
    from app.models.campaign import Enrollment
    from app.models.donor import Donor
    from app.models.response import DonorResponse
    from app.models.series import SeriesStep


class Message(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A rendered message in a donor's simulator chat thread."""

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_donor_id_created_at", "donor_id", "created_at"),
        Index("ix_messages_status_scheduled_at", "status", "scheduled_at"),
    )

    donor_id: Mapped[UUID] = mapped_column(ForeignKey("donors.id"), nullable=False, index=True)
    enrollment_id: Mapped[UUID | None] = mapped_column(ForeignKey("enrollments.id"), index=True)
    step_id: Mapped[UUID | None] = mapped_column(ForeignKey("series_steps.id"), index=True)
    direction: Mapped[MessageDirection] = mapped_column(MESSAGE_DIRECTION_DB, nullable=False)
    kind: Mapped[MessageKind] = mapped_column(MESSAGE_KIND_DB, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[MediaType] = mapped_column(MEDIA_TYPE_DB, nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(500))
    buttons: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB)
    reply_to_message_id: Mapped[UUID | None] = mapped_column(ForeignKey("messages.id"), index=True)
    button_id: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[MessageStatus] = mapped_column(MESSAGE_STATUS_DB, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_reason: Mapped[str | None] = mapped_column(String(120))
    provider_message_id: Mapped[str | None] = mapped_column(String(120))

    donor: Mapped["Donor"] = relationship(back_populates="messages")
    enrollment: Mapped["Enrollment | None"] = relationship(back_populates="messages")
    step: Mapped["SeriesStep | None"] = relationship(back_populates="messages")
    reply_to_message: Mapped["Message | None"] = relationship(remote_side="Message.id")
    donor_response: Mapped["DonorResponse | None"] = relationship(back_populates="message")
