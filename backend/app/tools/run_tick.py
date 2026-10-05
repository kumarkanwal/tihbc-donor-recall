"""Run one scheduler tick for local demo verification."""

import asyncio
from dataclasses import asdict

import structlog

from app.core.clock import clock
from app.core.config import get_settings
from app.core.db import create_database_resources
from app.core.logging import configure_logging
from app.core.redis import create_redis_client
from app.scheduler.factory import build_scheduler_tick
from app.services.events.redis import RedisEventPublisher

logger = structlog.get_logger(__name__)


async def run() -> None:
    """Build and execute one scheduler tick."""
    settings = get_settings()
    if not settings.demo_mode:
        raise RuntimeError("Manual scheduler ticks require DEMO_MODE=true")
    resources = create_database_resources(settings.database_url)
    redis = create_redis_client(settings.redis_url)
    try:
        result = await build_scheduler_tick(
            resources.session_factory,
            settings,
            clock,
            RedisEventPublisher(redis, clock),
        ).run()
        logger.info("manual_scheduler_tick_finished", **asdict(result))
    finally:
        await redis.aclose()
        await resources.engine.dispose()


def main() -> None:
    """Configure logging and run one tick."""
    settings = get_settings()
    configure_logging(settings.log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
