"""Transactional sending of the next due content-series step."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.messaging.base import MessagingProvider, OutboundButton, ProviderSendResult
from app.models.campaign import Enrollment
from app.models.enums import (
    CampaignStatus,
    EnrollmentStatus,
    MessageDirection,
    MessageKind,
    MessageStatus,
    SeriesKind,
)
from app.models.message import Message
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.message import MessageRepository
from app.services.appointments.service import AppointmentService
from app.services.events.base import EventPublisher
from app.services.events.campaign import publish_campaign_counts
from app.services.events.types import EventType
from app.services.messaging.payloads import (
    enrollment_payload,
    message_created_payload,
    message_status_payload,
)
from app.services.messaging.rendering import RenderedStep, render_step
from app.services.messaging.selection import SelectedStep, select_next_step

UNREACHABLE_REASON = "Simulated unreachable number"
SENDABLE_STATUSES = frozenset(
    {EnrollmentStatus.PENDING, EnrollmentStatus.IN_PRIMARY, EnrollmentStatus.IN_SECONDARY}
)
logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SendNextStepResult:
    """Outcome of one newly persisted outbound step."""

    message_id: UUID
    status: MessageStatus


class MessagingService:
    """Render, persist, send, and schedule one due enrollment step."""

    def __init__(
        self,
        session: AsyncSession,
        enrollment_repository: EnrollmentRepository,
        message_repository: MessageRepository,
        appointment_service: AppointmentService,
        provider: MessagingProvider,
        publisher: EventPublisher,
        current_clock: Clock,
        timezone_display: str,
    ) -> None:
        self._session = session
        self._enrollments = enrollment_repository
        self._messages = message_repository
        self._appointments = appointment_service
        self._provider = provider
        self._publisher = publisher
        self._clock = current_clock
        self._timezone_display = timezone_display

    async def send_next_step(self, enrollment_id: UUID) -> SendNextStepResult | None:
        """Send one due step exactly once under an enrollment row lock."""
        enrollment = await self._enrollments.get_for_messaging_update(enrollment_id)
        if enrollment is None:
            raise NotFoundError("Enrollment not found")
        now = self._clock.now()
        if not self._is_due(enrollment, now):
            await self._commit()
            return None
        selection = select_next_step(enrollment)
        if selection is None:
            await self._commit()
            return None
        if await self._messages.exists_for_step(enrollment.id, selection.step.id):
            await self._commit()
            return None
        appointment = await self._appointments.book_default(enrollment)
        rendered = render_step(enrollment, selection, appointment, self._timezone_display)
        message = self._new_message(enrollment, selection, rendered, now)
        await self._messages.add_message(message)
        if not enrollment.donor.sim_reachable:
            self._mark_unreachable(message, enrollment)
        else:
            sent_at = await self._send(message, enrollment, rendered)
            self._advance_enrollment(enrollment, selection, sent_at)
        await self._commit()
        self._log_send(message, enrollment)
        await self._publish_send(message, enrollment)
        return SendNextStepResult(message_id=message.id, status=message.status)

    def _is_due(self, enrollment: Enrollment, now: datetime) -> bool:
        return (
            enrollment.campaign.status == CampaignStatus.RUNNING
            and enrollment.status in SENDABLE_STATUSES
            and enrollment.responded_at is None
            and enrollment.next_action_at is not None
            and enrollment.next_action_at <= now
        )

    def _new_message(
        self,
        enrollment: Enrollment,
        selection: SelectedStep,
        rendered: RenderedStep,
        now: datetime,
    ) -> Message:
        return Message(
            donor_id=enrollment.donor_id,
            enrollment_id=enrollment.id,
            step_id=selection.step.id,
            direction=MessageDirection.OUTBOUND,
            kind=MessageKind.INTERACTIVE if rendered.buttons else MessageKind.TEMPLATE,
            body=rendered.body,
            media_type=selection.step.media_type,
            media_url=selection.step.media_url,
            buttons=list(rendered.buttons) or None,
            status=MessageStatus.QUEUED,
            scheduled_at=enrollment.next_action_at,
            created_at=now,
        )

    async def _send(
        self,
        message: Message,
        enrollment: Enrollment,
        rendered: RenderedStep,
    ) -> datetime:
        result = await self._provider_send(message, enrollment, rendered)
        message.status = MessageStatus.SENT
        sent_at = self._clock.now()
        message.sent_at = sent_at
        message.updated_at = sent_at
        message.provider_message_id = result.provider_message_id
        return sent_at

    async def _provider_send(
        self,
        message: Message,
        enrollment: Enrollment,
        rendered: RenderedStep,
    ) -> ProviderSendResult:
        if rendered.buttons:
            buttons = tuple(
                OutboundButton(id=button["id"], label=button["label"])
                for button in rendered.buttons
            )
            return await self._provider.send_interactive_message(
                message_id=message.id,
                recipient=enrollment.donor.phone_e164,
                body=rendered.body,
                buttons=buttons,
                media_type=message.media_type,
                media_url=message.media_url,
            )
        return await self._provider.send_template_message(
            message_id=message.id,
            recipient=enrollment.donor.phone_e164,
            body=rendered.body,
            media_type=message.media_type,
            media_url=message.media_url,
        )

    @staticmethod
    def _advance_enrollment(
        enrollment: Enrollment,
        selection: SelectedStep,
        sent_at: datetime,
    ) -> None:
        enrollment.status = (
            EnrollmentStatus.IN_SECONDARY
            if selection.series.kind == SeriesKind.SECONDARY
            else EnrollmentStatus.IN_PRIMARY
        )
        enrollment.current_series_kind = selection.series.kind
        enrollment.current_step_order = selection.step.step_order
        if selection.following_step is not None:
            enrollment.next_action_at = sent_at + timedelta(
                days=selection.following_step.delay_days
            )
        else:
            enrollment.next_action_at = sent_at + timedelta(
                hours=selection.series.response_window_hours
            )

    def _mark_unreachable(self, message: Message, enrollment: Enrollment) -> None:
        message.status = MessageStatus.FAILED
        message.failed_reason = UNREACHABLE_REASON
        message.updated_at = self._clock.now()
        enrollment.status = EnrollmentStatus.UNDELIVERABLE
        enrollment.next_action_at = None

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _log_send(message: Message, enrollment: Enrollment) -> None:
        event = "message_failed" if message.status == MessageStatus.FAILED else "message_sent"
        logger.info(
            event,
            message_id=str(message.id),
            enrollment_id=str(enrollment.id),
            campaign_id=str(enrollment.campaign_id),
            status=message.status.value,
            failed_reason=message.failed_reason,
        )

    async def _publish_send(self, message: Message, enrollment: Enrollment) -> None:
        await self._publisher.publish(
            EventType.MESSAGE_CREATED.value,
            message_created_payload(message),
        )
        if message.status == MessageStatus.FAILED:
            await self._publisher.publish(
                EventType.MESSAGE_STATUS_UPDATED.value,
                message_status_payload(message),
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
