"""Content series, message step, localized content, and tag models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    LANGUAGE_CODE_DB,
    MEDIA_TYPE_DB,
    MESSAGE_CATEGORY_DB,
    SERIES_KIND_DB,
    SERIES_STATUS_DB,
    LanguageCode,
    MediaType,
    MessageCategory,
    SeriesKind,
    SeriesStatus,
)

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.message import Message
    from app.models.user import User


series_tags = Table(
    "series_tags",
    Base.metadata,
    Column(
        "series_id",
        ForeignKey("content_series.id"),
        primary_key=True,
        index=True,
    ),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True, index=True),
)


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable content-series tag."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    series: Mapped[list["ContentSeries"]] = relationship(
        secondary=series_tags, back_populates="tags"
    )


class ContentSeries(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A versioned sequence of scheduled donor messages."""

    __tablename__ = "content_series"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[SeriesKind] = mapped_column(SERIES_KIND_DB, nullable=False)
    status: Mapped[SeriesStatus] = mapped_column(
        SERIES_STATUS_DB,
        nullable=False,
        default=SeriesStatus.DRAFT,
        server_default=text("'draft'::series_status"),
    )
    languages: Mapped[list[LanguageCode]] = mapped_column(ARRAY(LANGUAGE_CODE_DB), nullable=False)
    response_window_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=48, server_default="48"
    )
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    created_by: Mapped["User"] = relationship(back_populates="created_series")
    tags: Mapped[list[Tag]] = relationship(secondary=series_tags, back_populates="series")
    steps: Mapped[list["SeriesStep"]] = relationship(
        back_populates="series",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SeriesStep.step_order",
    )
    primary_campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="primary_series", foreign_keys="Campaign.primary_series_id"
    )
    secondary_campaigns: Mapped[list["Campaign"]] = relationship(
        back_populates="secondary_series", foreign_keys="Campaign.secondary_series_id"
    )


class SeriesStep(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One scheduled message in a content series."""

    __tablename__ = "series_steps"
    __table_args__ = (
        UniqueConstraint("series_id", "step_order"),
        CheckConstraint("step_order >= 1", name="step_order_positive"),
    )

    series_id: Mapped[UUID] = mapped_column(
        ForeignKey("content_series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[MessageCategory] = mapped_column(MESSAGE_CATEGORY_DB, nullable=False)
    media_type: Mapped[MediaType] = mapped_column(
        MEDIA_TYPE_DB,
        nullable=False,
        default=MediaType.NONE,
        server_default=text("'none'::media_type"),
    )
    media_url: Mapped[str | None] = mapped_column(String(500))
    buttons: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)

    series: Mapped[ContentSeries] = relationship(back_populates="steps")
    contents: Mapped[list["SeriesStepContent"]] = relationship(
        back_populates="step", cascade="all, delete-orphan", passive_deletes=True
    )
    messages: Mapped[list["Message"]] = relationship(back_populates="step")


class SeriesStepContent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Localized text for one content-series step."""

    __tablename__ = "series_step_contents"
    __table_args__ = (
        UniqueConstraint("step_id", "language"),
        CheckConstraint("char_length(body) <= 1024", name="body_max_length"),
    )

    step_id: Mapped[UUID] = mapped_column(
        ForeignKey("series_steps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[LanguageCode] = mapped_column(LANGUAGE_CODE_DB, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    step: Mapped[SeriesStep] = relationship(back_populates="contents")
