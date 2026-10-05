"""Secondary-series exhaustion and needs-call follow-up creation."""

from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidStateTransitionError
from app.models.campaign import Enrollment
from app.models.enums import (
    EnrollmentStatus,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.repositories.follow_up import FollowUpRepository
from app.services.events.base import EventPublisher
from app.services.events.campaign import publish_campaign_counts
from app.services.events.types import EventType
from app.services.follow_ups.payloads import follow_up_created_payload
from app.services.messaging.payloads import enrollment_payload

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class EscalationResult:
    """Result of idempotently escalating one enrollment."""

    follow_up_created: bool


class EscalationService:
    """Escalate an enrollment and ensure one open needs-call follow-up."""

    def __init__(
        self,
        session: AsyncSession,
        repository: FollowUpRepository,
        publisher: EventPublisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._publisher = publisher

    async def escalate(self, enrollment: Enrollment) -> EscalationResult:
        """Persist escalation and publish its committed changes."""
        if enrollment.status != EnrollmentStatus.IN_SECONDARY:
            raise InvalidStateTransitionError(
                "Enrollment must finish its secondary series before escalation",
                {"status": enrollment.status.value},
            )
        existing = await self._repository.open_for_enrollment(enrollment.id)
        follow_up = existing or self._new_follow_up(enrollment)
        created = existing is None
        if created:
            activity = FollowUpActivity(follow_up=follow_up, action="created")
            await self._repository.add_with_activity(follow_up, activity)
        else:
            follow_up.type = FollowUpType.NEEDS_CALL
            follow_up.priority = FollowUpPriority.HIGH
        enrollment.status = EnrollmentStatus.ESCALATED
        enrollment.next_action_at = None
        await self._commit()
        logger.info(
            "enrollment_escalated",
            enrollment_id=str(enrollment.id),
            campaign_id=str(enrollment.campaign_id),
            follow_up_id=str(follow_up.id),
        )
        await self._publisher.publish(
            (EventType.FOLLOWUP_CREATED.value if created else EventType.FOLLOWUP_UPDATED.value),
            follow_up_created_payload(follow_up),
        )
        await self._publisher.publish(
            EventType.ENROLLMENT_UPDATED.value,
            enrollment_payload(enrollment),
        )
        await self._publisher.publish(
            EventType.METRICS_UPDATED.value,
            {"campaign_id": str(enrollment.campaign_id)},
        )
        await publish_campaign_counts(self._session, enrollment, self._publisher)
        return EscalationResult(follow_up_created=created)

    @staticmethod
    def _new_follow_up(enrollment: Enrollment) -> FollowUpItem:
        return FollowUpItem(
            enrollment_id=enrollment.id,
            type=FollowUpType.NEEDS_CALL,
            status=FollowUpStatus.OPEN,
            priority=FollowUpPriority.HIGH,
        )

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
