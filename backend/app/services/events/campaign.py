"""Publish committed campaign counters after enrollment changes."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Enrollment
from app.repositories.enrollment import EnrollmentRepository
from app.services.events.base import EventPublisher
from app.ws.events import EventType


async def publish_campaign_counts(
    session: AsyncSession,
    enrollment: Enrollment,
    publisher: EventPublisher,
) -> None:
    """Read grouped counts and close the read transaction before publishing."""
    counts = await EnrollmentRepository(session).counts_by_status(enrollment.campaign_id)
    await session.commit()
    await publisher.publish(
        EventType.CAMPAIGN_UPDATED.value,
        {
            "id": str(enrollment.campaign_id),
            "status": enrollment.campaign.status.value,
            "counts": {status.value: count for status, count in counts.items()},
        },
    )
