"""Placeholder scheduler process until the dispatcher is implemented in Task 2.5."""

import asyncio
import signal
from types import FrameType

import structlog

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


async def heartbeat_loop(
    interval_seconds: float,
    shutdown_event: asyncio.Event,
) -> None:
    """Log worker liveness until shutdown is requested."""
    logger.info("scheduler_started", interval_seconds=interval_seconds)
    try:
        while not shutdown_event.is_set():
            logger.info("scheduler_heartbeat")
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                continue
    finally:
        logger.info("scheduler_stopped")


async def run_scheduler(settings: Settings) -> None:
    """Run the heartbeat worker and handle container termination signals."""
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
    await heartbeat_loop(settings.dispatcher_interval_seconds, shutdown_event)


def main() -> None:
    """Configure the scheduler process and run it to completion."""
    settings = get_settings()
    configure_logging(settings.log_level)
    asyncio.run(run_scheduler(settings))


if __name__ == "__main__":
    main()
