"""One resilient, idempotent scheduler polling tick."""

from dataclasses import asdict, dataclass
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import Clock, ClockPersistence
from app.core.config import Settings
from app.messaging.base import MessagingProvider
from app.repositories.appointment import AppointmentRepository
from app.repositories.campaign import CampaignRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.follow_up import FollowUpRepository
from app.repositories.message import MessageRepository
from app.repositories.scheduler import SchedulerRepository
from app.scheduler.enrollments import DueEnrollmentAction, DueEnrollmentService
from app.services.appointments.service import AppointmentService
from app.services.campaigns.service import CampaignService
from app.services.events.base import EventPublisher
from app.services.follow_ups.escalation import EscalationService
from app.services.messaging.delivery import DeliveryProgressionService
from app.services.messaging.service import MessagingService

logger = structlog.get_logger(__name__)


@dataclass
class TickSummary:
    """Count-only outcome of one scheduler tick."""

    campaigns_started: int = 0
    messages_sent: int = 0
    secondary_started: int = 0
    enrollments_escalated: int = 0
    campaigns_completed: int = 0
    messages_delivered: int = 0
    messages_read: int = 0
    failures: int = 0


class SchedulerTick:
    """Run campaign, enrollment, completion, and delivery phases in order."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
        current_clock: Clock,
        clock_persistence: ClockPersistence,
        provider: MessagingProvider,
        publisher: EventPublisher,
    ) -> None:
        self._sessions = session_factory
        self._settings = settings
        self._clock = current_clock
        self._clock_persistence = clock_persistence
        self._provider = provider
        self._publisher = publisher

    async def run(self) -> TickSummary:
        """Run one bounded tick and continue past isolated job failures."""
        await self._clock.initialize(self._clock_persistence)
        summary = TickSummary()
        summary.campaigns_started, failures = await self._start_campaigns()
        summary.failures += failures
        due_counts, failures = await self._process_enrollments()
        summary.messages_sent = due_counts[DueEnrollmentAction.MESSAGE_SENT]
        summary.secondary_started = due_counts[DueEnrollmentAction.SECONDARY_STARTED]
        summary.enrollments_escalated = due_counts[DueEnrollmentAction.ESCALATED]
        summary.failures += failures
        summary.campaigns_completed, failures = await self._complete_campaigns()
        summary.failures += failures
        delivered, read, failures = await self._advance_delivery()
        summary.messages_delivered = delivered
        summary.messages_read = read
        summary.failures += failures
        logger.info("scheduler_tick_completed", **asdict(summary))
        return summary

    async def _start_campaigns(self) -> tuple[int, int]:
        started = 0
        failures = 0
        excluded: set[UUID] = set()
        for _ in range(self._settings.dispatcher_batch_size):
            campaign_id: UUID | None = None
            try:
                async with self._sessions() as session:
                    campaign_id = await SchedulerRepository(session).next_scheduled_campaign(
                        self._clock.now(), frozenset(excluded)
                    )
                    if campaign_id is None:
                        break
                    await self._campaign_service(session).start_scheduled(campaign_id)
                started += 1
            except Exception as error:
                failures += 1
                self._log_job_failure("start_campaign", campaign_id, error)
                if campaign_id is not None:
                    excluded.add(campaign_id)
        return started, failures

    async def _process_enrollments(
        self,
    ) -> tuple[dict[DueEnrollmentAction, int], int]:
        counts = {action: 0 for action in DueEnrollmentAction}
        failures = 0
        excluded: set[UUID] = set()
        for _ in range(self._settings.dispatcher_batch_size):
            enrollment_id: UUID | None = None
            try:
                async with self._sessions() as session:
                    enrollment_id = await SchedulerRepository(session).next_due_enrollment(
                        self._clock.now(), frozenset(excluded)
                    )
                    if enrollment_id is None:
                        break
                    action = await self._due_service(session).process(enrollment_id)
                counts[action] += 1
                excluded.add(enrollment_id)
            except Exception as error:
                failures += 1
                self._log_job_failure("process_enrollment", enrollment_id, error)
                if enrollment_id is not None:
                    excluded.add(enrollment_id)
        return counts, failures

    async def _complete_campaigns(self) -> tuple[int, int]:
        completed = 0
        failures = 0
        excluded: set[UUID] = set()
        for _ in range(self._settings.dispatcher_batch_size):
            campaign_id: UUID | None = None
            try:
                async with self._sessions() as session:
                    campaign_id = await SchedulerRepository(session).next_completable_campaign(
                        frozenset(excluded)
                    )
                    if campaign_id is None:
                        break
                    await self._campaign_service(session).complete(campaign_id)
                completed += 1
            except Exception as error:
                failures += 1
                self._log_job_failure("complete_campaign", campaign_id, error)
                if campaign_id is not None:
                    excluded.add(campaign_id)
        return completed, failures

    async def _advance_delivery(self) -> tuple[int, int, int]:
        try:
            async with self._sessions() as session:
                result = await self._delivery_service(session).advance()
            return result.delivered, result.read, 0
        except Exception as error:
            self._log_job_failure("advance_delivery", None, error)
            return 0, 0, 1

    def _campaign_service(self, session: AsyncSession) -> CampaignService:
        return CampaignService(
            session,
            CampaignRepository(session),
            EnrollmentRepository(session),
            self._clock,
            self._publisher,
        )

    def _due_service(self, session: AsyncSession) -> DueEnrollmentService:
        enrollments = EnrollmentRepository(session)
        messaging = MessagingService(
            session,
            enrollments,
            MessageRepository(session),
            AppointmentService(
                AppointmentRepository(session),
                self._clock,
                self._settings.timezone_display,
            ),
            self._provider,
            self._publisher,
            self._clock,
            self._settings.timezone_display,
        )
        escalation = EscalationService(
            session,
            FollowUpRepository(session),
            self._publisher,
        )
        return DueEnrollmentService(enrollments, messaging, escalation, self._clock)

    def _delivery_service(self, session: AsyncSession) -> DeliveryProgressionService:
        return DeliveryProgressionService(
            session,
            MessageRepository(session),
            self._provider,
            self._publisher,
            self._clock,
            delivery_delay_seconds=self._settings.sim_delivery_delay_seconds,
            auto_read_delay_seconds=self._settings.sim_auto_read_delay_seconds,
            auto_read_rate=self._settings.sim_auto_read_rate,
        )

    @staticmethod
    def _log_job_failure(action: str, entity_id: UUID | None, error: Exception) -> None:
        logger.exception(
            "scheduler_job_failed",
            action=action,
            entity_id=str(entity_id) if entity_id else None,
            error_type=type(error).__name__,
        )
