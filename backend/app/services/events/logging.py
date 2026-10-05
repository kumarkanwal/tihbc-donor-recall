"""Logging-only event publisher used before Redis fan-out exists."""

from collections.abc import Mapping

import structlog

logger = structlog.get_logger(__name__)


class LoggingEventPublisher:
    """Record event metadata without an external delivery dependency."""

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        logger.info(
            "domain_event_published",
            event_type=event_type,
            entity_id=payload.get("id"),
        )
