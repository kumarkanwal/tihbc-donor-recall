"""Process one locked, due campaign enrollment."""

from enum import StrEnum
from uuid import UUID

from app.core.clock import Clock
from app.core.errors import InvalidStateTransitionError, NotFoundError
from app.models.campaign import Enrollment
from app.models.enums import EnrollmentStatus, SeriesKind
from app.repositories.enrollment import EnrollmentRepository
from app.services.follow_ups.escalation import EscalationService
from app.services.messaging.selection import select_next_step
from app.services.messaging.service import MessagingService


class DueEnrollmentAction(StrEnum):
    """Scheduler action completed for one due enrollment."""

    MESSAGE_SENT = "message_sent"
    SECONDARY_STARTED = "secondary_started"
    ESCALATED = "escalated"
    NO_OP = "no_op"


class DueEnrollmentService:
    """Own progression between message steps and escalation boundaries."""

    def __init__(
        self,
        enrollment_repository: EnrollmentRepository,
        messaging_service: MessagingService,
        escalation_service: EscalationService,
        current_clock: Clock,
    ) -> None:
        self._enrollments = enrollment_repository
        self._messaging = messaging_service
        self._escalation = escalation_service
        self._clock = current_clock

    async def process(self, enrollment_id: UUID) -> DueEnrollmentAction:
        """Process the next due action while the enrollment row is locked."""
        enrollment = await self._enrollments.get_for_messaging_update(enrollment_id)
        if enrollment is None:
            raise NotFoundError("Enrollment not found")
        if select_next_step(enrollment) is not None:
            result = await self._messaging.send_next_step(enrollment.id)
            return (
                DueEnrollmentAction.MESSAGE_SENT
                if result is not None
                else DueEnrollmentAction.NO_OP
            )
        if enrollment.current_series_kind == SeriesKind.PRIMARY:
            self._start_secondary(enrollment)
            result = await self._messaging.send_next_step(enrollment.id)
            return (
                DueEnrollmentAction.SECONDARY_STARTED
                if result is not None
                else DueEnrollmentAction.NO_OP
            )
        await self._escalation.escalate(enrollment)
        return DueEnrollmentAction.ESCALATED

    def _start_secondary(self, enrollment: Enrollment) -> None:
        if enrollment.status != EnrollmentStatus.IN_PRIMARY:
            raise InvalidStateTransitionError(
                "Enrollment must finish its primary series before secondary starts",
                {"status": enrollment.status.value},
            )
        enrollment.status = EnrollmentStatus.IN_SECONDARY
        enrollment.current_series_kind = SeriesKind.SECONDARY
        enrollment.current_step_order = None
        enrollment.next_action_at = self._clock.now()
