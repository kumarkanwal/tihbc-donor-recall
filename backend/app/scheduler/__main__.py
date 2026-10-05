"""Database-polling scheduler worker."""

import asyncio
import signal
from types import FrameType
from typing import Protocol

import structlog

from app.core.clock import clock
from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.logging import configure_logging
from app.core.redis import create_redis_client
from app.scheduler.factory import build_scheduler_tick
from app.scheduler.tick import TickSummary
from app.services.events.redis import RedisEventPublisher

logger = structlog.get_logger(__name__)


class TickRunner(Protocol):
    """One scheduler tick dependency."""

    async def run(self) -> TickSummary:
        """Run one scheduler tick."""


async def dispatcher_loop(
    tick: TickRunner,
    interval_seconds: float,
    shutdown_event: asyncio.Event,
) -> None:
    """Run ticks until shutdown, surviving tick-level failures."""
    logger.info("scheduler_started", interval_seconds=interval_seconds)
    try:
        while not shutdown_event.is_set():
            try:
                await tick.run()
            except Exception as error:
                logger.exception(
                    "scheduler_tick_failed",
                    error_type=type(error).__name__,
                )
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                continue
    finally:
        logger.info("scheduler_stopped")


async def run_scheduler(settings: Settings) -> None:
    """Create scheduler resources and handle worker termination signals."""
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_shutdown(signum: int, frame: FrameType | None) -> None:
        del signum, frame
        loop.call_soon_threadsafe(shutdown_event.set)

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, shutdown_event.set)
        except NotImplementedError:
            signal.signal(signum, request_shutdown)
    resources = create_database_resources(settings.database_url)
    redis = create_redis_client(settings.redis_url)
    try:
        tick = build_scheduler_tick(
            resources.session_factory,
            settings,
            clock,
            RedisEventPublisher(redis, clock),
        )
        await dispatcher_loop(tick, settings.dispatcher_interval_seconds, shutdown_event)
    finally:
        await redis.aclose()
        await resources.engine.dispose()


def main() -> None:
    """Configure the scheduler process and run it to completion."""
    settings = get_settings()
    configure_logging(settings.log_level)
    asyncio.run(run_scheduler(settings))


if __name__ == "__main__":
    main()
