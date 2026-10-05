"""PostgreSQL coverage for non-blocking messaging without appointment slots."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import MessageStatus
from app.models.message import Message
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.message import MessageRepository
from app.services.messaging.service import MessagingService
from tests.integration.messaging_fixtures import (
    FixedClock,
    RecordingProvider,
    RecordingPublisher,
    UnavailableAppointmentService,
    add_messaging_fixture,
)

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_no_appointment_slots_uses_fallback_and_still_sends(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
        provider = RecordingProvider()
        service = MessagingService(
            session,
            EnrollmentRepository(session),
            MessageRepository(session),
            UnavailableAppointmentService(),
            provider,
            RecordingPublisher(session),
            FixedClock(NOW),
            "Asia/Karachi",
        )

        result = await service.send_next_step(fixture.enrollment.id)

        assert result is not None
        message = await session.get(Message, result.message_id)
        assert message is not None
        assert message.status == MessageStatus.SENT
        assert message.body == (
            "Hello Campaign Donor 0 at Korangi Campus Blood Center on at your earliest convenience"
        )
        assert fixture.enrollment.appointment_slot_id is None
        assert provider.sends == [("interactive", message.id)]
