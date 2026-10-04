"""Complete SQLAlchemy model registry."""

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.campaign import AppointmentSlot, Campaign, Enrollment
from app.models.demo_clock import DemoClock
from app.models.donor import Donor, DonorBatch, Segment
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.models.message import Message
from app.models.response import DonorResponse
from app.models.series import ContentSeries, SeriesStep, SeriesStepContent, Tag, series_tags
from app.models.user import User

__all__ = [
    "AppointmentSlot",
    "Base",
    "Campaign",
    "ContentSeries",
    "DemoClock",
    "Donor",
    "DonorBatch",
    "DonorResponse",
    "Enrollment",
    "FollowUpActivity",
    "FollowUpItem",
    "Message",
    "Segment",
    "SeriesStep",
    "SeriesStepContent",
    "Tag",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "series_tags",
]
