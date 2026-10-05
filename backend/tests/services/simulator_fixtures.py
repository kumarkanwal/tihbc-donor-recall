"""Unit-test simulator models and repositories with no external services."""

from collections.abc import Mapping
from dataclasses import dataclass
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
from app.repositories.follow_up import FollowUpRepository
from app.repositories.response import DonorResponseRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.services.appointments.service import AppointmentService
from app.services.replies.flow import ReplyFlow
from app.services.reply_service import ReplyService
from tests.integration.messaging_fixtures import FixedClock, RecordingProvider

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


@dataclass
class ReplyFixture:
    """Mocks and models used by deterministic reply-service tests."""

    service: ReplyService
    session: AsyncMock
    donors: AsyncMock
    messages: AsyncMock
    enrollments: AsyncMock
    appointments: AsyncMock
    follow_ups: AsyncMock
    responses: AsyncMock
    provider: RecordingProvider
    publisher: Publisher
    sleep: AsyncMock
    person: Donor
    source: Message
    enrollment: Enrollment


def reply_service() -> ReplyFixture:
    session = AsyncMock(spec=AsyncSession)
    donors, messages = AsyncMock(spec=DonorRepository), AsyncMock(spec=SimulatorMessageRepository)
    enrollments = AsyncMock(spec=EnrollmentRepository)
    appointments = AsyncMock(spec=AppointmentService)
    follow_ups = AsyncMock(spec=FollowUpRepository)
    responses = AsyncMock(spec=DonorResponseRepository)
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
    enrollment.donor = person
    donors.get.return_value = person
    messages.get.return_value = source
    messages.latest_outbound.return_value = source
    messages.has_reply.return_value = False
    enrollments.get_for_messaging_update.return_value = enrollment
    follow_ups.open_for_enrollment.return_value = None
    appointments.offer.return_value = ()
    responses.unknown_count.return_value = 1

    async def persist_follow_up(item: object, activity: object) -> None:
        del activity
        item.id = uuid4()
        item.created_at = NOW
        item.updated_at = NOW

    follow_ups.add_with_activity.side_effect = persist_follow_up

    async def persist(item: Message) -> Message:
        item.id = uuid4()
        return item

    messages.add.side_effect = persist
    publisher = Publisher(session)
    provider = RecordingProvider()
    sleep = AsyncMock()
    service = ReplyService(
        session,
        donors,
        messages,
        enrollments,
        ReplyFlow(appointments, follow_ups, responses, "Asia/Karachi"),
        provider,
        publisher,
        FixedClock(NOW),
        "Asia/Karachi",
        typing_seconds=1.5,
        sleep=sleep,
    )
    return ReplyFixture(
        service,
        session,
        donors,
        messages,
        enrollments,
        appointments,
        follow_ups,
        responses,
        provider,
        publisher,
        sleep,
        person,
        source,
        enrollment,
    )
