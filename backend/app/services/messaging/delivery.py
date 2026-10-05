"""Deterministic simulator delivery and read progression."""

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.messaging.base import MessagingProvider
from app.models.enums import MessageStatus
from app.models.message import Message
from app.repositories.message import MessageRepository
from app.services.events.base import EventPublisher
from app.services.events.types import EventType
from app.services.messaging.payloads import message_status_payload

RATE_BUCKETS = 10_000


@dataclass(frozen=True)
class DeliveryProgressionResult:
    """Counts changed by one delivery-progression pass."""

    delivered: int
    read: int


class DeliveryProgressionService:
    """Advance due simulator messages through delivered and read states."""

    def __init__(
        self,
        session: AsyncSession,
        repository: MessageRepository,
        provider: MessagingProvider,
        publisher: EventPublisher,
        current_clock: Clock,
        *,
        delivery_delay_seconds: float,
        auto_read_delay_seconds: float,
        auto_read_rate: float,
    ) -> None:
        self._session = session
        self._repository = repository
        self._provider = provider
        self._publisher = publisher
        self._clock = current_clock
        self._delivery_delay = timedelta(seconds=delivery_delay_seconds)
        self._read_delay = timedelta(seconds=auto_read_delay_seconds)
        self._auto_read_rate = auto_read_rate

    async def advance(self) -> DeliveryProgressionResult:
        """Advance all currently due messages and publish after commit."""
        now = self._clock.now()
        delivered = await self._repository.sent_due_for_delivery(now - self._delivery_delay)
        read_candidates = await self._repository.delivered_due_for_read(now - self._read_delay)
        read = tuple(
            message
            for message in read_candidates
            if should_auto_read(message.id, self._auto_read_rate)
        )
        for message in delivered:
            message.status = MessageStatus.DELIVERED
            message.delivered_at = now
            message.updated_at = now
        for message in read:
            message.status = MessageStatus.READ
            message.read_at = now
            message.updated_at = now
        await self._commit()
        for message in (*delivered, *read):
            await self._report_and_publish(message)
        return DeliveryProgressionResult(delivered=len(delivered), read=len(read))

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _report_and_publish(self, message: Message) -> None:
        if message.provider_message_id is not None:
            await self._provider.report_status_update(
                provider_message_id=message.provider_message_id,
                status=message.status,
            )
        await self._publisher.publish(
            EventType.MESSAGE_STATUS_UPDATED.value,
            message_status_payload(message),
        )
        await self._publisher.publish(
            EventType.METRICS_UPDATED.value,
            {
                "campaign_id": (
                    str(message.enrollment.campaign_id) if message.enrollment is not None else None
                )
            },
        )


def should_auto_read(message_id: UUID, rate: float) -> bool:
    """Select a stable message share without randomness or persisted flags."""
    threshold = round(rate * RATE_BUCKETS)
    return message_id.int % RATE_BUCKETS < threshold
