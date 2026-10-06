"""Transactional donor reply handling after deterministic or agent classification."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.messaging.base import MessagingProvider, OutboundButton, ProviderSendResult
from app.models.campaign import Enrollment
from app.models.enums import MediaType, MessageDirection, MessageKind, MessageStatus
from app.models.message import Message
from app.models.response import DonorResponse
from app.repositories.donor import DonorRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.schemas.simulator import ButtonReply, SimulatorMessage, SimulatorReply
from app.services.events.base import EventPublisher
from app.services.follow_ups.payloads import follow_up_created_payload
from app.services.messaging.payloads import enrollment_payload, message_created_payload
from app.services.replies.classification import Classification
from app.services.replies.classifier import ReplyClassifier
from app.services.replies.flow import FlowOutcome, ReplyFlow
from app.services.replies.templates import render_reply
from app.ws.events import EventType

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ReplyEventPayloads:
    """Public event snapshots captured before ORM state can expire."""

    inbound: dict[str, object]
    outbound: dict[str, object]
    enrollment: dict[str, object]
    follow_up: dict[str, object]
    enrollment_id: str
    donor_id: str
    campaign_id: str
    follow_up_created: bool


class ReplyService:
    """Classify one inbound reply and apply its complete conversation flow."""

    def __init__(
        self,
        session: AsyncSession,
        donors: DonorRepository,
        messages: SimulatorMessageRepository,
        enrollments: EnrollmentRepository,
        classifier: ReplyClassifier,
        flow: ReplyFlow,
        provider: MessagingProvider,
        publisher: EventPublisher,
        current_clock: Clock,
        timezone_display: str,
        *,
        typing_seconds: float,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._session = session
        self._donors = donors
        self._messages = messages
        self._enrollments = enrollments
        self._classifier = classifier
        self._flow = flow
        self._provider = provider
        self._publisher = publisher
        self._clock = current_clock
        self._timezone_display = timezone_display
        self._typing_seconds = typing_seconds
        self._sleep = sleep

    async def reply(self, donor_id: UUID, request: SimulatorReply) -> SimulatorMessage:
        """Persist, classify, respond, commit, then publish ordered events."""
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
        classification = await self._classifier.classify(request, source, donor, enrollment)
        inbound = await self._store_inbound(enrollment, source, request, body)
        self._store_response(enrollment, inbound, classification)
        self._stop_outreach(enrollment)
        outcome = await self._flow.apply(enrollment, classification, body)
        outbound = await self._store_automatic_reply(enrollment, outcome)
        payloads = await self._event_payloads(enrollment, inbound, outbound, outcome)
        result = SimulatorMessage.model_validate(payloads.inbound)
        await self._commit()
        await self._publish(payloads)
        logger.info(
            "donor_reply_applied",
            enrollment_id=payloads.enrollment_id,
            campaign_id=payloads.campaign_id,
            intent=classification.intent.value,
            source=classification.source.value,
        )
        return result

    async def _source(self, donor_id: UUID, request: SimulatorReply) -> Message:
        source = (
            await self._messages.get(request.reply_to_message_id)
            if isinstance(request, ButtonReply)
            else await self._messages.latest_outbound(donor_id)
        )
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

    async def _store_inbound(
        self,
        enrollment: Enrollment,
        source: Message,
        request: SimulatorReply,
        body: str,
    ) -> Message:
        now = self._clock.now()
        message = Message(
            donor_id=enrollment.donor_id,
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
        return message

    def _store_response(
        self, enrollment: Enrollment, inbound: Message, classification: Classification
    ) -> None:
        self._session.add(
            DonorResponse(
                enrollment_id=enrollment.id,
                message_id=inbound.id,
                intent=classification.intent,
                source=classification.source,
                detected_language=classification.detected_language,
                requested_date=classification.requested_date,
                decline_reason=classification.decline_reason,
                confidence=classification.confidence,
                trace_id=classification.trace_id,
            )
        )

    def _stop_outreach(self, enrollment: Enrollment) -> None:
        enrollment.next_action_at = None
        enrollment.responded_at = enrollment.responded_at or self._clock.now()

    async def _store_automatic_reply(self, enrollment: Enrollment, outcome: FlowOutcome) -> Message:
        now = self._clock.now()
        body = render_reply(
            outcome.template_key,
            enrollment,
            outcome.appointment,
            self._timezone_display,
        )
        message = Message(
            donor_id=enrollment.donor_id,
            enrollment_id=enrollment.id,
            direction=MessageDirection.OUTBOUND,
            kind=MessageKind.INTERACTIVE if outcome.buttons else MessageKind.TEXT,
            body=body,
            media_type=MediaType.NONE,
            buttons=outcome.buttons or None,
            status=MessageStatus.QUEUED,
            scheduled_at=now,
            created_at=now,
        )
        await self._messages.add(message)
        result = await self._send(message, enrollment, outcome)
        message.status = MessageStatus.SENT
        sent_at = self._clock.now()
        message.sent_at = sent_at
        message.updated_at = sent_at
        message.provider_message_id = result.provider_message_id
        return message

    async def _send(
        self, message: Message, enrollment: Enrollment, outcome: FlowOutcome
    ) -> ProviderSendResult:
        if outcome.buttons:
            return await self._provider.send_interactive_message(
                message_id=message.id,
                recipient=enrollment.donor.phone_e164,
                body=message.body,
                buttons=tuple(
                    OutboundButton(id=str(item["id"]), label=str(item["label"]))
                    for item in outcome.buttons
                ),
                media_type=MediaType.NONE,
                media_url=None,
            )
        return await self._provider.send_text_message(
            message_id=message.id,
            recipient=enrollment.donor.phone_e164,
            body=message.body,
        )

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _event_payloads(
        self,
        enrollment: Enrollment,
        inbound: Message,
        outbound: Message,
        outcome: FlowOutcome,
    ) -> ReplyEventPayloads:
        await self._session.flush()
        await self._session.refresh(outcome.follow_up, attribute_names=["created_at", "updated_at"])
        return ReplyEventPayloads(
            inbound=message_created_payload(inbound),
            outbound=message_created_payload(outbound),
            enrollment=enrollment_payload(enrollment),
            follow_up=follow_up_created_payload(outcome.follow_up),
            enrollment_id=str(enrollment.id),
            donor_id=str(enrollment.donor_id),
            campaign_id=str(enrollment.campaign_id),
            follow_up_created=outcome.follow_up_created,
        )

    async def _publish(self, payloads: ReplyEventPayloads) -> None:
        await self._publisher.publish(
            EventType.SIMULATOR_TYPING.value,
            {"donor_id": payloads.donor_id, "is_typing": True},
        )
        await self._sleep(self._typing_seconds)
        await self._publisher.publish(EventType.MESSAGE_CREATED.value, payloads.inbound)
        await self._publisher.publish(EventType.MESSAGE_CREATED.value, payloads.outbound)
        await self._publisher.publish(
            EventType.SIMULATOR_TYPING.value,
            {"donor_id": payloads.donor_id, "is_typing": False},
        )
        await self._publisher.publish(EventType.ENROLLMENT_UPDATED.value, payloads.enrollment)
        event = (
            EventType.FOLLOWUP_CREATED.value
            if payloads.follow_up_created
            else EventType.FOLLOWUP_UPDATED.value
        )
        await self._publisher.publish(event, payloads.follow_up)
        await self._publisher.publish(
            EventType.METRICS_UPDATED.value,
            {"campaign_id": payloads.campaign_id},
        )
