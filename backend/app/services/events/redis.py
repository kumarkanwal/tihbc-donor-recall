"""Redis transport for committed domain events."""

from collections.abc import Mapping
from typing import Protocol, cast

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.clock import Clock
from app.ws.events import EVENT_CHANNEL, EventEnvelope, EventType, public_payload

logger = structlog.get_logger(__name__)


class RedisPublishClient(Protocol):
    """Minimal publish capability, also usable by worker processes."""

    async def publish(self, channel: str, message: str) -> int:
        """Publish one serialized envelope."""


class RedisEventPublisher:
    """Publish public envelopes without undoing committed writes on outage."""

    def __init__(
        self,
        redis: Redis | RedisPublishClient,
        current_clock: Clock,
        *,
        channel: str = EVENT_CHANNEL,
    ) -> None:
        # redis-py's command mixin combines sync/async stubs; runtime client is async.
        self._redis = cast(RedisPublishClient, redis)
        self._clock = current_clock
        self._channel = channel

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        """Validate and publish an event after the caller's commit."""
        kind = EventType(event_type)
        envelope = EventEnvelope(
            type=kind,
            payload=public_payload(kind, payload),
            ts=self._clock.now(),
        )
        try:
            await self._redis.publish(self._channel, envelope.model_dump_json())
        except RedisError:
            logger.exception("domain_event_publish_failed", event_type=event_type)
