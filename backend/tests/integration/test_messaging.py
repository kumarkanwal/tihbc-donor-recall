"""PostgreSQL coverage for message sending and simulated delivery."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import EnrollmentStatus, LanguageCode, MessageStatus, SeriesKind
from app.models.message import Message
from app.repositories.appointment import AppointmentRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.message import MessageRepository
from app.services.appointments.service import AppointmentService
from app.services.events.types import EventType
from app.services.messaging.delivery import DeliveryProgressionService
from app.services.messaging.service import UNREACHABLE_REASON, MessagingService
from tests.integration.messaging_fixtures import (
    FixedClock,
    RecordingProvider,
    RecordingPublisher,
    add_messaging_fixture,
)

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_send_next_step_renders_updates_and_is_idempotent(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
        provider = RecordingProvider()
        publisher = RecordingPublisher(session)
        service = _messaging_service(session, FixedClock(NOW), provider, publisher)

        result = await service.send_next_step(fixture.enrollment.id)

        assert result is not None
        message = await session.get(Message, result.message_id)
        assert message is not None
        assert message.status == MessageStatus.SENT
        assert message.body == (
            "Hello Campaign Donor 0 at Korangi Campus Blood Center on Tue 6 Oct, 10:00 AM"
        )
        assert message.buttons == [{"id": "btn_confirm", "intent": "confirm", "label": "Confirm"}]
        assert message.provider_message_id == f"test-{message.id}"
        assert fixture.enrollment.status == EnrollmentStatus.IN_PRIMARY
        assert fixture.enrollment.current_step_order == 1
        assert fixture.enrollment.next_action_at == NOW + timedelta(days=3)
        assert fixture.enrollment.appointment_slot_id == fixture.default_slot.id
        assert fixture.default_slot.booked_count == 1
        assert provider.sends == [("interactive", message.id)]
        assert [event_type for event_type, _payload in publisher.events] == [
            EventType.MESSAGE_CREATED.value,
            EventType.ENROLLMENT_UPDATED.value,
            EventType.METRICS_UPDATED.value,
        ]
        created_payload = publisher.events[0][1]
        assert created_payload["buttons"] == [{"id": "btn_confirm", "label": "Confirm"}]
        assert "enrollment_id" not in created_payload
        assert created_payload["button_id"] is None
        assert created_payload["reply_to_message_id"] is None

        duplicate = await service.send_next_step(fixture.enrollment.id)
        message_count = await session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.enrollment_id == fixture.enrollment.id)
        )

        assert duplicate is None
        assert message_count == 1
        assert len(provider.sends) == 1


@pytest.mark.asyncio
async def test_secondary_step_and_urdu_rendering(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW, language=LanguageCode.UR)
        fixture.enrollment.status = EnrollmentStatus.IN_SECONDARY
        fixture.enrollment.current_series_kind = SeriesKind.SECONDARY
        await session.commit()
        provider = RecordingProvider()
        service = _messaging_service(
            session,
            FixedClock(NOW),
            provider,
            RecordingPublisher(session),
        )

        result = await service.send_next_step(fixture.enrollment.id)

        assert result is not None
        message = await session.get(Message, result.message_id)
        assert message is not None
        assert message.step_id == fixture.secondary_step.id
        assert message.body == (
            "Campaign Donor 0، Korangi Campus Blood Center، منگل ۶ اکتوبر، صبح ۱۰ بجے"
        )
        assert fixture.enrollment.status == EnrollmentStatus.IN_SECONDARY
        assert fixture.enrollment.current_step_order == 1
        assert fixture.enrollment.next_action_at == NOW + timedelta(hours=48)
        assert provider.sends == [("template", message.id)]


@pytest.mark.asyncio
async def test_unreachable_donor_fails_and_stops_steps(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW, reachable=False)
        await session.commit()
        provider = RecordingProvider()
        publisher = RecordingPublisher(session)

        result = await _messaging_service(
            session,
            FixedClock(NOW),
            provider,
            publisher,
        ).send_next_step(fixture.enrollment.id)

        assert result is not None
        message = await session.get(Message, result.message_id)
        assert message is not None
        assert message.status == MessageStatus.FAILED
        assert message.failed_reason == UNREACHABLE_REASON
        assert message.sent_at is None
        assert fixture.enrollment.status == EnrollmentStatus.UNDELIVERABLE
        assert fixture.enrollment.next_action_at is None
        assert provider.sends == []
        assert EventType.MESSAGE_STATUS_UPDATED.value in {
            event_type for event_type, _payload in publisher.events
        }


@pytest.mark.asyncio
async def test_delivery_progresses_with_clock_and_read_receipts(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
        provider = RecordingProvider()
        publisher = RecordingPublisher(session)
        send_clock = FixedClock(NOW)
        sent = await _messaging_service(
            session,
            send_clock,
            provider,
            publisher,
        ).send_next_step(fixture.enrollment.id)
        assert sent is not None
        publisher.events.clear()
        delivery_clock = FixedClock(NOW + timedelta(seconds=1))
        delivery = DeliveryProgressionService(
            session,
            MessageRepository(session),
            provider,
            publisher,
            delivery_clock,
            delivery_delay_seconds=2,
            auto_read_delay_seconds=10,
            auto_read_rate=1,
        )

        early = await delivery.advance()
        delivery_clock.value = NOW + timedelta(seconds=2)
        delivered = await delivery.advance()
        delivery_clock.value = NOW + timedelta(seconds=12)
        read = await delivery.advance()

        message = await session.get(Message, sent.message_id)
        assert message is not None
        assert early.delivered == early.read == 0
        assert delivered.delivered == 1
        assert delivered.read == 0
        assert read.read == 1
        assert message.status == MessageStatus.READ
        assert message.delivered_at == NOW + timedelta(seconds=2)
        assert message.read_at == NOW + timedelta(seconds=12)
        assert [status for _provider_id, status in provider.status_reports] == [
            MessageStatus.DELIVERED,
            MessageStatus.READ,
        ]
        assert [event for event, _payload in publisher.events].count(
            EventType.MESSAGE_STATUS_UPDATED.value
        ) == 2


@pytest.mark.asyncio
async def test_delivery_never_reads_when_donor_disables_receipts(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW, read_receipts=False)
        await session.commit()
        provider = RecordingProvider()
        publisher = RecordingPublisher(session)
        sent = await _messaging_service(
            session,
            FixedClock(NOW),
            provider,
            publisher,
        ).send_next_step(fixture.enrollment.id)
        assert sent is not None
        delivery_clock = FixedClock(NOW + timedelta(minutes=1))
        delivery = DeliveryProgressionService(
            session,
            MessageRepository(session),
            provider,
            publisher,
            delivery_clock,
            delivery_delay_seconds=2,
            auto_read_delay_seconds=10,
            auto_read_rate=1,
        )

        await delivery.advance()
        delivery_clock.value += timedelta(minutes=1)
        result = await delivery.advance()

        message = await session.get(Message, sent.message_id)
        assert message is not None
        assert message.status == MessageStatus.DELIVERED
        assert result.read == 0


@pytest.mark.asyncio
async def test_events_are_not_published_when_commit_fails(
    postgres_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
        publisher = RecordingPublisher(session)
        monkeypatch.setattr(session, "commit", AsyncMock(side_effect=RuntimeError("commit failed")))

        with pytest.raises(RuntimeError, match="commit failed"):
            await _messaging_service(
                session,
                FixedClock(NOW),
                RecordingProvider(),
                publisher,
            ).send_next_step(fixture.enrollment.id)

        assert publisher.events == []


def _messaging_service(
    session: AsyncSession,
    current_clock: FixedClock,
    provider: RecordingProvider,
    publisher: RecordingPublisher,
) -> MessagingService:
    return MessagingService(
        session,
        EnrollmentRepository(session),
        MessageRepository(session),
        AppointmentService(
            AppointmentRepository(session),
            current_clock,
            "Asia/Karachi",
        ),
        provider,
        publisher,
        current_clock,
        "Asia/Karachi",
    )
