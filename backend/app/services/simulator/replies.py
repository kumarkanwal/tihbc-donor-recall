"""Transactional inbound reply capture, without classifying intent."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.campaign import Enrollment
from app.models.enums import MediaType, MessageDirection, MessageKind, MessageStatus
from app.models.message import Message
from app.repositories.donor import DonorRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.schemas.simulator import ButtonReply, SimulatorMessage, SimulatorReply
from app.services.events.base import EventPublisher
from app.services.messaging.payloads import enrollment_payload, message_created_payload
from app.ws.events import EventType


class SimulatorReplyService:
    """Persist replies and stop scheduled outreach under the enrollment lock."""

    def __init__(
        self,
        session: AsyncSession,
        donors: DonorRepository,
        messages: SimulatorMessageRepository,
        enrollments: EnrollmentRepository,
        publisher: EventPublisher,
        current_clock: Clock,
    ) -> None:
        self._session = session
        self._donors = donors
        self._messages = messages
        self._enrollments = enrollments
        self._publisher = publisher
        self._clock = current_clock

    async def reply(self, donor_id: UUID, request: SimulatorReply) -> SimulatorMessage:
        """Capture a localized button reply or text and publish after commit."""
        donor = await self._donors.get(donor_id)
        if donor is None:
            raise NotFoundError("Donor not found")
        if not donor.sim_reachable:
            raise ConflictError("Donor is unreachable")
        source = await self._source(donor_id, request)
        if source.enrollment_id is None:
            raise ConflictError("Message has no campaign enrollment")
        enrollment = await self._enrollments.get_for_messaging_update(source.enrollment_id)
        if enrollment is None:
            raise NotFoundError("Enrollment not found")
        body = await self._body(source, request)
        now = self._clock.now()
        message = Message(
            donor_id=donor_id,
            enrollment_id=enrollment.id,
            direction=MessageDirection.INBOUND,
            kind=MessageKind.BUTTON_REPLY if isinstance(request, ButtonReply) else MessageKind.TEXT,
            body=body,
            media_type=MediaType.NONE,
            status=MessageStatus.DELIVERED,
            reply_to_message_id=source.id,
            button_id=request.button_id if isinstance(request, ButtonReply) else None,
            scheduled_at=now,
            sent_at=now,
            delivered_at=now,
            created_at=now,
            updated_at=now,
        )
        await self._messages.add(message)
        self._stop_outreach(enrollment)
        await self._session.commit()
        result = SimulatorMessage.model_validate(message_created_payload(message))
        await self._publisher.publish(
            EventType.MESSAGE_CREATED.value, result.model_dump(mode="json")
        )
        await self._publisher.publish(
            EventType.ENROLLMENT_UPDATED.value, enrollment_payload(enrollment)
        )
        await self._publisher.publish(
            EventType.METRICS_UPDATED.value, {"campaign_id": str(enrollment.campaign_id)}
        )
        return result

    async def _source(self, donor_id: UUID, request: SimulatorReply) -> Message:
        if isinstance(request, ButtonReply):
            source = await self._messages.get(request.reply_to_message_id)
        else:
            source = await self._messages.latest_outbound(donor_id)
        if source is None:
            raise ValidationError("No outbound message is available for this reply")
        if (
            source.donor_id != donor_id
            or source.direction != MessageDirection.OUTBOUND
            or source.status
            not in {MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.READ}
        ):
            raise ValidationError("Reply must reference this donor's sent outbound message")
        return source

    async def _body(self, source: Message, request: SimulatorReply) -> str:
        if not isinstance(request, ButtonReply):
            return request.text
        if await self._messages.has_reply(source.id):
            raise ConflictError("This message has already received a reply")
        for button in source.buttons or []:
            if button.get("id") == request.button_id and isinstance(button.get("label"), str):
                return str(button["label"])
        raise ValidationError("Button does not belong to this message")

    def _stop_outreach(self, enrollment: Enrollment) -> None:
        """Suspend future steps; classification and final status belong to Task 2.8."""
        enrollment.next_action_at = None
        enrollment.responded_at = enrollment.responded_at or self._clock.now()
