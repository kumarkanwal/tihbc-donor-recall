"""Advance due simulator delivery and read states in demo mode."""

import asyncio

import structlog

from app.core.clock import clock
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.messaging.dependencies import build_delivery_service
from app.tools.runtime import event_publisher, messaging_session

logger = structlog.get_logger(__name__)


async def run() -> None:
    """Advance all due simulator messages once."""
    settings = get_settings()
    configure_logging(settings.log_level)
    async with messaging_session(settings) as session, event_publisher(settings) as publisher:
        result = await build_delivery_service(session, settings, clock, publisher).advance()
    logger.info(
        "delivery_progression_finished",
        delivered=result.delivered,
        read=result.read,
    )


def main() -> None:
    """Run one delivery progression pass."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
