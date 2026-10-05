"""Simulator read receipts without changing queued or sent messages."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.models.enums import MessageStatus
from app.repositories.donor import DonorRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.schemas.simulator import OpenConversationResult
from app.services.events.base import EventPublisher
from app.services.messaging.payloads import message_status_payload
from app.ws.events import EventType


class SimulatorReceiptService:
    """Own the delivered-to-read transition when a conversation is opened."""

    def __init__(
        self,
        session: AsyncSession,
        donors: DonorRepository,
        messages: SimulatorMessageRepository,
        publisher: EventPublisher,
        current_clock: Clock,
    ) -> None:
        self._session = session
        self._donors = donors
        self._messages = messages
        self._publisher = publisher
        self._clock = current_clock

    async def open(self, donor_id: UUID) -> OpenConversationResult:
        """Mark delivered outreach as read only when read receipts are enabled."""
        donor = await self._donors.get(donor_id)
        if donor is None:
            raise NotFoundError("Donor not found")
        if not donor.sim_read_receipts:
            await self._session.commit()
            return OpenConversationResult(read_count=0)
        messages = await self._messages.delivered_outbound_for_update(donor_id)
        now = self._clock.now()
        for message in messages:
            message.status = MessageStatus.READ
            message.read_at = now
            message.updated_at = now
        await self._session.commit()
        campaign_ids = set()
        for message in messages:
            await self._publisher.publish(
                EventType.MESSAGE_STATUS_UPDATED.value,
                message_status_payload(message),
            )
            campaign_ids.add(str(message.enrollment.campaign_id) if message.enrollment else None)
        for campaign_id in campaign_ids:
            await self._publisher.publish(
                EventType.METRICS_UPDATED.value, {"campaign_id": campaign_id}
            )
        return OpenConversationResult(read_count=len(messages))
