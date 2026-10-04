"""Staff user model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import USER_ROLE_DB, UserRole

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.donor import DonorBatch
    from app.models.follow_up import FollowUpActivity, FollowUpItem
    from app.models.series import ContentSeries


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A TIHBC staff account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(USER_ROLE_DB, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    uploaded_batches: Mapped[list["DonorBatch"]] = relationship(back_populates="uploaded_by")
    created_series: Mapped[list["ContentSeries"]] = relationship(back_populates="created_by")
    created_campaigns: Mapped[list["Campaign"]] = relationship(back_populates="created_by")
    assigned_follow_ups: Mapped[list["FollowUpItem"]] = relationship(
        back_populates="assigned_to", foreign_keys="FollowUpItem.assigned_to_id"
    )
    resolved_follow_ups: Mapped[list["FollowUpItem"]] = relationship(
        back_populates="resolved_by", foreign_keys="FollowUpItem.resolved_by_id"
    )
    follow_up_activities: Mapped[list["FollowUpActivity"]] = relationship(back_populates="user")
