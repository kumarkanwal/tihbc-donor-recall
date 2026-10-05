"""PostgreSQL coverage for the complete scheduler lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import Clock
from app.models.campaign import Campaign, Enrollment
from app.models.enums import CampaignStatus, EnrollmentStatus, MessageStatus
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.models.message import Message
from app.services.events.types import EventType
from tests.integration.messaging_fixtures import (
    FixedClock,
    RecordingProvider,
    add_messaging_fixture,
)
from tests.integration.scheduler_fixtures import (
    CollectingPublisher,
    MutableClockPersistence,
    build_test_tick,
)

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_tick_runs_full_primary_secondary_escalation_lifecycle(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
    current_clock = FixedClock(NOW)
    provider = RecordingProvider()
    publisher = CollectingPublisher()
    tick = build_test_tick(postgres_session_factory, current_clock, provider, publisher)

    day_zero = await tick.run()
    current_clock.value = NOW + timedelta(days=3)
    day_three = await tick.run()
    current_clock.value = NOW + timedelta(days=5)
    day_five = await tick.run()
    current_clock.value = NOW + timedelta(days=7)
    day_seven = await tick.run()
    repeated = await tick.run()

    async with postgres_session_factory() as session:
        enrollment = await session.get(Enrollment, fixture.enrollment.id)
        campaign = await session.get(Campaign, fixture.campaign.id)
        messages = tuple(
            await session.scalars(
                select(Message)
                .where(Message.enrollment_id == fixture.enrollment.id)
                .order_by(Message.sent_at)
            )
        )
        follow_up = await session.scalar(
            select(FollowUpItem).where(FollowUpItem.enrollment_id == fixture.enrollment.id)
        )
        assert follow_up is not None
        activity_count = await session.scalar(
            select(func.count())
            .select_from(FollowUpActivity)
            .where(FollowUpActivity.follow_up_id == follow_up.id)
        )

    assert day_zero.messages_sent == 1
    assert day_three.messages_sent == 1
    assert day_five.secondary_started == 1
    assert day_seven.enrollments_escalated == 1
    assert day_seven.campaigns_completed == 1
    assert repeated.enrollments_escalated == 0
    assert repeated.campaigns_completed == 0
    assert enrollment is not None and enrollment.status == EnrollmentStatus.ESCALATED
    assert enrollment.next_action_at is None
    assert campaign is not None and campaign.status == CampaignStatus.COMPLETED
    assert campaign.completed_at == current_clock.value
    assert len(messages) == 3
    assert all(
        message.status in {MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.READ}
        for message in messages
    )
    assert follow_up.type.value == "needs_call"
    assert follow_up.priority.value == "high"
    assert activity_count == 1
    event_types = {event_type for event_type, _payload in publisher.events}
    assert EventType.FOLLOWUP_CREATED.value in event_types
    assert EventType.CAMPAIGN_UPDATED.value in event_types


@pytest.mark.asyncio
async def test_each_tick_reloads_offset_and_stamps_messages_with_demo_time(
    postgres_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.core.clock.wall_clock_now", lambda: NOW)
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
    current_clock = Clock()
    persistence = MutableClockPersistence()
    tick = build_test_tick(
        postgres_session_factory,
        current_clock,
        RecordingProvider(),
        clock_persistence=persistence,
    )

    await tick.run()
    persistence.offset_seconds = int(timedelta(days=3).total_seconds())
    await tick.run()

    async with postgres_session_factory() as session:
        messages = tuple(
            await session.scalars(
                select(Message)
                .where(Message.enrollment_id == fixture.enrollment.id)
                .order_by(Message.sent_at)
            )
        )
    assert persistence.load_calls == 2
    assert [message.sent_at for message in messages] == [NOW, NOW + timedelta(days=3)]
    assert [message.created_at for message in messages] == [NOW, NOW + timedelta(days=3)]


@pytest.mark.asyncio
async def test_scheduled_campaign_starts_and_paused_campaign_is_skipped(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        scheduled = await add_messaging_fixture(session, NOW)
        paused = await add_messaging_fixture(session, NOW)
        scheduled.campaign.status = CampaignStatus.SCHEDULED
        paused.campaign.status = CampaignStatus.PAUSED
        await session.commit()
    tick = build_test_tick(postgres_session_factory, FixedClock(NOW), RecordingProvider())

    result = await tick.run()

    async with postgres_session_factory() as session:
        scheduled_campaign = await session.get(Campaign, scheduled.campaign.id)
        scheduled_enrollment = await session.get(Enrollment, scheduled.enrollment.id)
        paused_campaign = await session.get(Campaign, paused.campaign.id)
        paused_enrollment = await session.get(Enrollment, paused.enrollment.id)
    assert result.campaigns_started == 1
    assert scheduled_campaign is not None
    assert scheduled_campaign.status == CampaignStatus.RUNNING
    assert scheduled_enrollment is not None
    assert scheduled_enrollment.status == EnrollmentStatus.IN_PRIMARY
    assert paused_campaign is not None and paused_campaign.status == CampaignStatus.PAUSED
    assert paused_enrollment is not None
    assert paused_enrollment.status == EnrollmentStatus.PENDING


@pytest.mark.asyncio
async def test_unreachable_enrollment_finishes_campaign(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW, reachable=False)
        await session.commit()
    tick = build_test_tick(postgres_session_factory, FixedClock(NOW), RecordingProvider())

    result = await tick.run()

    async with postgres_session_factory() as session:
        enrollment = await session.get(Enrollment, fixture.enrollment.id)
        campaign = await session.get(Campaign, fixture.campaign.id)
        message = await session.scalar(
            select(Message).where(Message.enrollment_id == fixture.enrollment.id)
        )
    assert result.messages_sent == 1
    assert result.campaigns_completed == 1
    assert enrollment is not None and enrollment.status == EnrollmentStatus.UNDELIVERABLE
    assert campaign is not None and campaign.status == CampaignStatus.COMPLETED
    assert message is not None and message.status == MessageStatus.FAILED
