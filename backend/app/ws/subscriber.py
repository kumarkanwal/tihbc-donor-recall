"""Redis subscription and process-local metrics coalescing."""

import asyncio
from contextlib import suppress

import structlog
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.ws.events import EVENT_CHANNEL, METRICS_DEBOUNCE_SECONDS, EventEnvelope, EventType
from app.ws.manager import ConnectionManager

logger = structlog.get_logger(__name__)
RECONNECT_SECONDS = 1.0


class EventDispatcher:
    """Broadcast events; coalesce metrics by campaign over two seconds."""

    def __init__(
        self,
        manager: ConnectionManager,
        *,
        debounce_seconds: float = METRICS_DEBOUNCE_SECONDS,
    ) -> None:
        self._manager = manager
        self._delay = debounce_seconds
        self._pending: dict[str, EventEnvelope] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._active: set[asyncio.Task[None]] = set()

    async def dispatch(self, data: str) -> None:
        """Ignore unknown/malformed events without logging their contents."""
        try:
            event = EventEnvelope.model_validate_json(data).public()
        except (ValidationError, ValueError):
            logger.debug("websocket_event_ignored")
            return
        if event.type != EventType.METRICS_UPDATED:
            await self._manager.broadcast(event)
            return
        key = str(event.payload["campaign_id"])
        self._pending[key] = event
        if key not in self._tasks:
            task = asyncio.create_task(self._flush(key))
            self._tasks[key] = task
            self._active.add(task)
            task.add_done_callback(self._active.discard)

    async def _flush(self, key: str) -> None:
        await asyncio.sleep(self._delay)
        event = self._pending.pop(key)
        # Release the window before awaiting I/O so a new event starts a fresh window.
        self._tasks.pop(key, None)
        await self._manager.broadcast(event)

    async def shutdown(self) -> None:
        """Flush invalidations and drain background tasks."""
        tasks = tuple(self._active)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        for event in self._pending.values():
            await self._manager.broadcast(event)
        self._pending.clear()


class RedisEventSubscriber:
    """Subscribe each API process to the worker/API channel."""

    def __init__(
        self,
        redis: Redis,
        dispatcher: EventDispatcher,
        *,
        channel: str = EVENT_CHANNEL,
    ) -> None:
        self._redis = redis
        self._channel = channel
        self._dispatcher = dispatcher
        self._task: asyncio.Task[None] | None = None
        self.ready = asyncio.Event()

    async def start(self) -> None:
        """Start a managed listener with outage retry."""
        self._task = asyncio.create_task(self._listen())
        try:
            await asyncio.wait_for(self.ready.wait(), timeout=5)
        except TimeoutError:
            logger.warning("websocket_subscription_not_ready")

    async def _listen(self) -> None:
        while True:
            try:
                async with self._redis.pubsub() as subscription:
                    await subscription.subscribe(self._channel)
                    async for message in subscription.listen():
                        if message["type"] == "subscribe":
                            self.ready.set()
                        if message["type"] == "message" and isinstance(message["data"], str):
                            await self._dispatcher.dispatch(message["data"])
            except RedisError:
                self.ready.clear()
                logger.exception("websocket_subscription_failed")
                await asyncio.sleep(RECONNECT_SECONDS)

    async def stop(self) -> None:
        """Cancel the reader and flush pending invalidations."""
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        await self._dispatcher.shutdown()
