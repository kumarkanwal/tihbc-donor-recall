"""PostgreSQL-only constraint and clock persistence tests."""

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import Clock, clock
from app.models.campaign import AppointmentSlot, Campaign, Enrollment
from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import (
    CampaignStatus,
    EnrollmentStatus,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
    LanguageCode,
    SeriesKind,
    UserRole,
)
from app.models.follow_up import FollowUpItem
from app.models.series import ContentSeries
from app.models.user import User
from app.repositories.demo_clock import DatabaseClockPersistence

pytestmark = pytest.mark.postgres


async def _create_donor_context(session: AsyncSession) -> tuple[User, DonorBatch, Donor]:
    segment = await session.scalar(select(Segment).where(Segment.key == "regular"))
    assert segment is not None
    token = uuid4().hex
    user = User(
        email=f"integration-{token}@example.test",
        full_name="Integration User",
        password_hash="not-a-real-password-hash",
        role=UserRole.ADMIN,
    )
    batch = DonorBatch(
        name=f"Integration batch {token}",
        original_filename="integration.csv",
        uploaded_by=user,
        total_rows=1,
        valid_rows=1,
        invalid_rows=0,
        validation_report=[],
    )
    donor = Donor(
        batch=batch,
        full_name="Integration Donor",
        phone_e164="+923000000001",
        segment=segment,
        language=LanguageCode.EN,
    )
    session.add_all((user, batch, donor))
    await session.flush()
    return user, batch, donor


async def _create_enrollment(session: AsyncSession) -> Enrollment:
    user, batch, donor = await _create_donor_context(session)
    token = uuid4().hex
    primary = ContentSeries(
        name=f"Primary {token}",
        kind=SeriesKind.PRIMARY,
        languages=[LanguageCode.EN],
        created_by=user,
    )
    secondary = ContentSeries(
        name=f"Secondary {token}",
        kind=SeriesKind.SECONDARY,
        languages=[LanguageCode.EN],
        created_by=user,
    )
    campaign = Campaign(
        name=f"Campaign {token}",
        batch=batch,
        primary_series=primary,
        secondary_series=secondary,
        status=CampaignStatus.DRAFT,
        start_at=clock.now(),
        created_by=user,
    )
    enrollment = Enrollment(
        campaign=campaign,
        donor=donor,
        status=EnrollmentStatus.PENDING,
    )
    session.add_all((primary, secondary, campaign, enrollment))
    await session.flush()
    return enrollment


@pytest.mark.asyncio
async def test_phone_is_unique_within_batch(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory.begin() as session:
        _, batch, donor = await _create_donor_context(session)
        duplicate = Donor(
            batch_id=batch.id,
            full_name="Duplicate Donor",
            phone_e164=donor.phone_e164,
            segment_id=donor.segment_id,
            language=LanguageCode.EN,
        )
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(duplicate)
                await session.flush()


@pytest.mark.asyncio
async def test_only_one_open_follow_up_per_enrollment(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory.begin() as session:
        enrollment = await _create_enrollment(session)
        first = FollowUpItem(
            enrollment=enrollment,
            type=FollowUpType.CONFIRMED,
            status=FollowUpStatus.OPEN,
            priority=FollowUpPriority.NORMAL,
        )
        session.add(first)
        await session.flush()
        duplicate = FollowUpItem(
            enrollment_id=enrollment.id,
            type=FollowUpType.RESCHEDULE,
            status=FollowUpStatus.IN_PROGRESS,
            priority=FollowUpPriority.NORMAL,
        )
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(duplicate)
                await session.flush()


@pytest.mark.asyncio
async def test_slot_booked_count_cannot_exceed_capacity(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory.begin() as session:
        invalid_slot = AppointmentSlot(
            center_name="Integration Center",
            starts_at=clock.now(),
            capacity=1,
            booked_count=2,
        )
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(invalid_slot)
                await session.flush()


@pytest.mark.asyncio
async def test_clock_offset_persists_across_instances(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    persistence = DatabaseClockPersistence(postgres_session_factory)
    first_clock = Clock()
    await first_clock.initialize(persistence)
    await first_clock.reset()
    await first_clock.advance(timedelta(days=3, hours=2))

    restarted_clock = Clock()
    await restarted_clock.initialize(DatabaseClockPersistence(postgres_session_factory))

    assert restarted_clock.offset == timedelta(days=3, hours=2)
    await restarted_clock.reset()


@pytest.mark.asyncio
async def test_reference_segments_exist(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        keys = set(await session.scalars(select(Segment.key)))
    assert {"first_time", "lapsed", "regular"} <= keys
