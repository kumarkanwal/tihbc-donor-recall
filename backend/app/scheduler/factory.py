"""Scheduler composition shared by workers, APIs, and tools."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import Clock
from app.core.config import Settings
from app.messaging.factory import create_messaging_provider
from app.repositories.demo_clock import DatabaseClockPersistence
from app.scheduler.tick import SchedulerTick
from app.services.events.base import EventPublisher


def build_scheduler_tick(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    current_clock: Clock,
    publisher: EventPublisher,
) -> SchedulerTick:
    """Build the configured scheduler tick."""
    return SchedulerTick(
        session_factory,
        settings,
        current_clock,
        DatabaseClockPersistence(session_factory),
        create_messaging_provider(settings.messaging_provider),
        publisher,
    )
