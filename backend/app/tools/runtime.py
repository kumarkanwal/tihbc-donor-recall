"""Shared database and demo-clock lifecycle for messaging tools."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import clock
from app.core.config import Settings
from app.core.db import create_database_resources
from app.core.redis import create_redis_client
from app.repositories.demo_clock import DatabaseClockPersistence
from app.services.events.redis import RedisEventPublisher


@asynccontextmanager
async def messaging_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """Yield a session with the persisted demo clock initialized."""
    if not settings.demo_mode:
        raise RuntimeError("Messaging demo tools require DEMO_MODE=true")
    resources = create_database_resources(settings.database_url)
    try:
        await clock.initialize(DatabaseClockPersistence(resources.session_factory))
        async with resources.session_factory() as session:
            yield session
    finally:
        await resources.engine.dispose()


@asynccontextmanager
async def event_publisher(settings: Settings) -> AsyncIterator[RedisEventPublisher]:
    """Own a Redis publisher for one CLI invocation."""
    redis = create_redis_client(settings.redis_url)
    try:
        yield RedisEventPublisher(redis, clock)
    finally:
        await redis.aclose()
