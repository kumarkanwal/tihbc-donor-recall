"""Persisted demo clock offset model."""

from sqlalchemy import BigInteger, CheckConstraint, SmallInteger, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DemoClock(TimestampMixin, Base):
    """The singleton persisted demo-clock offset."""

    __tablename__ = "demo_clock"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_id"),)

    id: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, default=1, server_default=text("1")
    )
    offset_seconds: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
