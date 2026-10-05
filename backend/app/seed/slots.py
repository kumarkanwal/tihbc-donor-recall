"""Idempotently seed demo appointment slots."""

import asyncio
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, clock
from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.logging import configure_logging
from app.models.campaign import AppointmentSlot
from app.repositories.appointment import AppointmentRepository
from app.repositories.demo_clock import DatabaseClockPersistence
from app.services.appointments.centers import DEMO_CENTERS

logger = structlog.get_logger(__name__)
SLOT_DAYS = 21
SLOT_HOURS = range(9, 17)
SLOT_CAPACITY = 4


async def seed_appointment_slots(
    session: AsyncSession,
    current_clock: Clock,
    timezone_display: str,
) -> int:
    """Create missing demo slots without changing existing bookings."""
    timezone = ZoneInfo(timezone_display)
    first_date = current_clock.now().astimezone(timezone).date()
    starts_at = _slot_time(first_date, 9, timezone)
    before = _slot_time(first_date + timedelta(days=SLOT_DAYS), 9, timezone)
    repository = AppointmentRepository(session)
    existing = await repository.existing_keys(starts_at=starts_at, before=before)
    slots = [
        AppointmentSlot(
            center_name=center,
            starts_at=_slot_time(first_date + timedelta(days=day), hour, timezone),
            capacity=SLOT_CAPACITY,
            booked_count=(day + hour) % SLOT_CAPACITY,
        )
        for day in range(SLOT_DAYS)
        for center in DEMO_CENTERS
        for hour in SLOT_HOURS
        if (center, _slot_time(first_date + timedelta(days=day), hour, timezone)) not in existing
    ]
    await repository.add_many(slots)
    return len(slots)


async def run(settings: Settings) -> int:
    """Initialize the demo clock and seed slots in one transaction."""
    if not settings.demo_mode:
        raise RuntimeError("Appointment slot seeding requires DEMO_MODE=true")
    resources = create_database_resources(settings.database_url)
    try:
        await clock.initialize(DatabaseClockPersistence(resources.session_factory))
        async with resources.session_factory.begin() as session:
            created = await seed_appointment_slots(session, clock, settings.timezone_display)
        logger.info("appointment_slots_seeded", created=created)
        return created
    finally:
        await resources.engine.dispose()


def _slot_time(day: date, hour: int, timezone: ZoneInfo) -> datetime:
    return datetime.combine(day, time(hour=hour), tzinfo=timezone).astimezone(UTC)


def main() -> None:
    """Run the appointment-slot seed command."""
    settings = get_settings()
    configure_logging(settings.log_level)
    asyncio.run(run(settings))


if __name__ == "__main__":
    main()
