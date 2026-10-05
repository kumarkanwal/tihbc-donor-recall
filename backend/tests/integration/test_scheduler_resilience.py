"""PostgreSQL coverage for scheduler isolation and concurrency."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.models.campaign import AppointmentSlot, Campaign, Enrollment
from app.models.donor import Donor, DonorBatch
from app.models.enums import (
    EnrollmentStatus,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
)
from app.models.message import Message
from app.models.series import ContentSeries, SeriesStep, SeriesStepContent
from app.models.user import User
from app.scheduler.tick import TickSummary
from tests.integration.messaging_fixtures import (
    FixedClock,
    MessagingFixture,
    RecordingProvider,
    add_messaging_fixture,
)
from tests.integration.scheduler_fixtures import (
    BlockingProvider,
    FailFirstProvider,
    build_test_tick,
)

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_failing_enrollment_does_not_stop_later_enrollments(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        first = await add_messaging_fixture(session, NOW)
        second = await add_messaging_fixture(session, NOW)
        await session.commit()
    provider = FailFirstProvider()
    tick = build_test_tick(postgres_session_factory, FixedClock(NOW), provider)

    result = await tick.run()

    enrollment_ids = (first.enrollment.id, second.enrollment.id)
    async with postgres_session_factory() as session:
        statuses = tuple(
            await session.scalars(
                select(Enrollment.status).where(Enrollment.id.in_(enrollment_ids))
            )
        )
        message_count = await session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.enrollment_id.in_(enrollment_ids))
        )
    assert result.failures == 1
    assert result.messages_sent == 1
    assert sorted(statuses) == sorted((EnrollmentStatus.PENDING, EnrollmentStatus.IN_PRIMARY))
    assert message_count == 1


@pytest.mark.asyncio
async def test_idempotent_no_op_does_not_starve_later_enrollments(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        duplicate = await add_messaging_fixture(session, NOW)
        later = await add_messaging_fixture(session, NOW)
        duplicate.enrollment.next_action_at = NOW - timedelta(minutes=1)
        session.add(
            Message(
                donor_id=duplicate.enrollment.donor_id,
                enrollment_id=duplicate.enrollment.id,
                step_id=duplicate.primary_steps[0].id,
                direction=MessageDirection.OUTBOUND,
                kind=MessageKind.TEMPLATE,
                body="Already sent",
                media_type=MediaType.NONE,
                status=MessageStatus.SENT,
                scheduled_at=NOW,
                sent_at=NOW,
            )
        )
        await session.commit()
    provider = RecordingProvider()
    tick = build_test_tick(postgres_session_factory, FixedClock(NOW), provider)

    result = await tick.run()

    async with postgres_session_factory() as session:
        later_message_count = await session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.enrollment_id == later.enrollment.id)
        )
    assert result.messages_sent == 1
    assert len(provider.sends) == 1
    assert later_message_count == 1


@pytest.mark.asyncio
async def test_two_concurrent_ticks_never_double_send() -> None:
    engine = create_async_engine(Settings().database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    fixture: MessagingFixture | None = None
    first_task: asyncio.Task[TickSummary] | None = None
    provider = BlockingProvider()
    try:
        async with session_factory() as session:
            fixture = await add_messaging_fixture(session, NOW)
            await session.commit()
        first_tick = build_test_tick(session_factory, FixedClock(NOW), provider)
        second_tick = build_test_tick(session_factory, FixedClock(NOW), provider)

        first_task = asyncio.create_task(first_tick.run())
        await asyncio.wait_for(provider.entered.wait(), timeout=5)
        second_result = await asyncio.wait_for(second_tick.run(), timeout=5)
        provider.release.set()
        first_result = await first_task

        async with session_factory() as session:
            message_count = await session.scalar(
                select(func.count())
                .select_from(Message)
                .where(Message.enrollment_id == fixture.enrollment.id)
            )
        assert first_result.messages_sent + second_result.messages_sent == 1
        assert len(provider.sends) == 1
        assert message_count == 1
    finally:
        provider.release.set()
        if first_task is not None and not first_task.done():
            await asyncio.gather(first_task, return_exceptions=True)
        if fixture is not None:
            await _delete_fixture(session_factory, fixture)
        await engine.dispose()


async def _delete_fixture(
    session_factory: async_sessionmaker[AsyncSession],
    fixture: MessagingFixture,
) -> None:
    enrollment_id = fixture.enrollment.id
    campaign_id = fixture.campaign.id
    step_ids = tuple(step.id for step in (*fixture.primary_steps, fixture.secondary_step))
    series_ids = (fixture.campaign_fixture.primary.id, fixture.campaign_fixture.secondary.id)
    donor_ids = tuple(donor.id for donor in fixture.campaign_fixture.donors)
    async with session_factory.begin() as session:
        await session.execute(delete(Message).where(Message.enrollment_id == enrollment_id))
        await session.execute(delete(Enrollment).where(Enrollment.id == enrollment_id))
        await session.execute(
            delete(AppointmentSlot).where(AppointmentSlot.id == fixture.default_slot.id)
        )
        await session.execute(delete(Campaign).where(Campaign.id == campaign_id))
        await session.execute(
            delete(SeriesStepContent).where(SeriesStepContent.step_id.in_(step_ids))
        )
        await session.execute(delete(SeriesStep).where(SeriesStep.id.in_(step_ids)))
        await session.execute(delete(Donor).where(Donor.id.in_(donor_ids)))
        await session.execute(delete(ContentSeries).where(ContentSeries.id.in_(series_ids)))
        await session.execute(
            delete(DonorBatch).where(DonorBatch.id == fixture.campaign_fixture.batch.id)
        )
        await session.execute(delete(User).where(User.id == fixture.campaign_fixture.user.id))
