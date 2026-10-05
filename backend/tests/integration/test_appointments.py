"""PostgreSQL coverage for appointment capacity and slot seeding."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.campaign import AppointmentSlot
from app.repositories.appointment import AppointmentRepository
from app.seed.slots import seed_appointment_slots
from app.services.appointments.service import AppointmentService
from tests.integration.messaging_fixtures import FixedClock, add_messaging_fixture

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_booking_skips_full_slot_and_does_not_double_book(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        fixture.default_slot.booked_count = fixture.default_slot.capacity
        fallback = AppointmentSlot(
            center_name=fixture.default_slot.center_name,
            starts_at=fixture.default_slot.starts_at + timedelta(hours=1),
            capacity=4,
            booked_count=3,
        )
        session.add(fallback)
        await session.flush()
        service = AppointmentService(AppointmentRepository(session), "Asia/Karachi")

        first = await service.book_default(fixture.enrollment)
        second = await service.book_default(fixture.enrollment)

        assert first.id == fallback.id
        assert second.id == fallback.id
        assert fallback.booked_count == 4
        assert fixture.default_slot.booked_count == 4


@pytest.mark.asyncio
async def test_slot_seed_is_idempotent_without_assuming_empty_database(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        before = await session.scalar(select(func.count()).select_from(AppointmentSlot))

        created = await seed_appointment_slots(session, FixedClock(NOW), "Asia/Karachi")
        after_first = await session.scalar(select(func.count()).select_from(AppointmentSlot))
        repeated = await seed_appointment_slots(session, FixedClock(NOW), "Asia/Karachi")
        after_second = await session.scalar(select(func.count()).select_from(AppointmentSlot))

        assert after_first == (before or 0) + created
        assert repeated == 0
        assert after_second == after_first
