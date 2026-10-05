"""Send one enrollment's next due message in demo mode."""

import argparse
import asyncio
from uuid import UUID

import structlog

from app.core.clock import clock
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.messaging.dependencies import build_messaging_service
from app.tools.runtime import event_publisher, messaging_session

logger = structlog.get_logger(__name__)


async def run(enrollment_id: UUID) -> None:
    """Send one due enrollment step and log its non-sensitive outcome."""
    settings = get_settings()
    configure_logging(settings.log_level)
    async with messaging_session(settings) as session, event_publisher(settings) as publisher:
        result = await build_messaging_service(session, settings, clock, publisher).send_next_step(
            enrollment_id
        )
    logger.info(
        "send_next_step_finished",
        enrollment_id=str(enrollment_id),
        message_id=str(result.message_id) if result else None,
        status=result.status.value if result else "not_due",
    )


def main() -> None:
    """Parse CLI arguments and send one due step."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enrollment", type=UUID, required=True)
    arguments = parser.parse_args()
    asyncio.run(run(arguments.enrollment))


if __name__ == "__main__":
    main()
