"""Unit-test simulator models and repositories with no external services."""

from collections.abc import Mapping
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Enrollment
from app.models.donor import Donor
from app.models.enums import (
    EnrollmentStatus,
    LanguageCode,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    SeriesKind,
)
from app.models.message import Message
from app.repositories.donor import DonorRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.services.simulator.replies import SimulatorReplyService
from tests.integration.messaging_fixtures import FixedClock

NOW = datetime(2026, 10, 5, tzinfo=UTC)


class Publisher:
    """Assert committed publication and collect payloads."""

    def __init__(self, session: AsyncMock) -> None:
        self.session = session
        self.events: list[tuple[str, Mapping[str, object]]] = []

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        assert self.session.commit.await_count > 0
        self.events.append((event_type, payload))


def donor() -> Donor:
    return Donor(
        id=uuid4(),
        full_name="Test Donor",
        phone_e164="+923001234567",
        language=LanguageCode.UR,
        sim_reachable=True,
        sim_read_receipts=True,
    )


def message(person: Donor, *, status: MessageStatus = MessageStatus.DELIVERED) -> Message:
    return Message(
        id=uuid4(),
        donor_id=person.id,
        enrollment_id=uuid4(),
        direction=MessageDirection.OUTBOUND,
        kind=MessageKind.INTERACTIVE,
        body="Reminder",
        media_type=MediaType.NONE,
        status=status,
        buttons=[{"id": "confirm", "label": "تصدیق کریں", "intent": "confirm"}],
        scheduled_at=NOW,
        sent_at=NOW,
        delivered_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )


def reply_service() -> tuple[
    SimulatorReplyService,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    Publisher,
    Donor,
    Message,
    Enrollment,
]:
    session = AsyncMock(spec=AsyncSession)
    donors, messages = AsyncMock(spec=DonorRepository), AsyncMock(spec=SimulatorMessageRepository)
    enrollments = AsyncMock(spec=EnrollmentRepository)
    person = donor()
    source = message(person)
    enrollment = Enrollment(
        id=source.enrollment_id,
        donor_id=person.id,
        campaign_id=uuid4(),
        status=EnrollmentStatus.IN_PRIMARY,
        current_series_kind=SeriesKind.PRIMARY,
        current_step_order=1,
        next_action_at=NOW,
    )
    donors.get.return_value = person
    messages.get.return_value = source
    messages.latest_outbound.return_value = source
    messages.has_reply.return_value = False
    enrollments.get_for_messaging_update.return_value = enrollment

    async def persist(item: Message) -> Message:
        item.id = uuid4()
        return item

    messages.add.side_effect = persist
    publisher = Publisher(session)
    service = SimulatorReplyService(
        session, donors, messages, enrollments, publisher, FixedClock(NOW)
    )
    return service, session, donors, messages, enrollments, publisher, person, source, enrollment
