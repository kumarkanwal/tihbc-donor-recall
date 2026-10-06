"""Full transactional demo dataset orchestration."""

import asyncio
from dataclasses import asdict, dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, clock
from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.logging import configure_logging
from app.repositories.demo_clock import DatabaseClockPersistence
from app.repositories.demo_reset import DemoResetRepository
from app.seed.campaigns import seed_campaigns
from app.seed.conversations import seed_conversations
from app.seed.donors import seed_batches_and_donors
from app.seed.sample_workbook import generate_sample_workbook
from app.seed.series import seed_content_series
from app.seed.slots import seed_appointment_slots
from app.seed.users import configured_seed_users, upsert_demo_users

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SeedSummary:
    """Non-personal counts produced by a complete demo seed."""

    users: int
    appointment_slots: int
    donors: int
    content_series: int
    campaigns: int
    messages: int
    responses: int
    follow_ups: int


async def seed_demo_data(
    session: AsyncSession,
    settings: Settings,
    current_clock: Clock,
) -> SeedSummary:
    """Populate a cleared transaction with the complete deterministic demo dataset."""
    now = current_clock.now()
    users = await upsert_demo_users(session, configured_seed_users(settings))
    slot_count = await seed_appointment_slots(session, current_clock, settings.timezone_display)
    batches = await seed_batches_and_donors(session, users[0], now)
    series = await seed_content_series(session, users[0], settings, now)
    campaigns = await seed_campaigns(session, batches, series, users[0], now)
    message_count, response_count, follow_up_count = await seed_conversations(
        session,
        campaigns,
        users[1],
        now,
        settings.timezone_display,
    )
    return SeedSummary(
        users=len(users),
        appointment_slots=slot_count,
        donors=(
            len(batches.regular_donors)
            + len(batches.lapsed_donors)
            + len(batches.first_time_donors)
        ),
        content_series=len(series),
        campaigns=3,
        messages=message_count,
        responses=response_count,
        follow_ups=follow_up_count,
    )


async def reset_and_seed_demo_data(
    session: AsyncSession,
    settings: Settings,
    current_clock: Clock,
    reset_repository: DemoResetRepository,
) -> SeedSummary:
    """Clear operational data and rebuild the complete dataset without committing."""
    await reset_repository.truncate_demo_data()
    return await seed_demo_data(session, settings, current_clock)


async def run(settings: Settings) -> SeedSummary:
    """Reset and seed the configured demo database in one transaction."""
    if not settings.demo_mode:
        raise RuntimeError("Demo seeding requires DEMO_MODE=true")
    resources = create_database_resources(settings.database_url)
    try:
        await clock.initialize(DatabaseClockPersistence(resources.session_factory))
        generate_sample_workbook()
        async with resources.session_factory.begin() as session:
            summary = await reset_and_seed_demo_data(
                session,
                settings,
                clock,
                DemoResetRepository(session),
            )
        logger.info("demo_data_seeded", **asdict(summary))
        return summary
    finally:
        await resources.engine.dispose()


async def main() -> None:
    """Run the complete seed command."""
    settings = get_settings()
    configure_logging(settings.log_level)
    await run(settings)


if __name__ == "__main__":
    asyncio.run(main())
