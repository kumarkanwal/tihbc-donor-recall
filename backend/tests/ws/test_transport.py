"""Public envelopes, isolated broadcast, and metrics debounce."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.clock import clock
from app.services.events.redis import RedisEventPublisher
from app.ws.events import EVENT_CHANNEL, EventEnvelope, EventType
from app.ws.manager import ConnectionManager
from app.ws.subscriber import EventDispatcher
from tests.integration.messaging_fixtures import FixedClock

NOW = datetime(2026, 10, 5, tzinfo=UTC)


class Socket:
    """Record frames or simulate a disconnected client."""

    def __init__(self, *, failed: bool = False) -> None:
        self.frames: list[str] = []
        self.failed = failed
        self.closed = False
        self.received = asyncio.Event()

    async def send_text(self, data: str) -> None:
        if self.failed:
            raise RuntimeError("disconnected")
        self.frames.append(data)
        self.received.set()

    async def close(self, code: int = 1000) -> None:
        self.closed = True


class RedisRecorder:
    """Record published envelopes without a server."""

    def __init__(self, *, failed: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.failed = failed

    async def publish(self, channel: str, message: str) -> int:
        if self.failed:
            raise RedisConnectionError("offline")
        self.calls.append((channel, message))
        return 1


def clock_event() -> EventEnvelope:
    return EventEnvelope(
        type=EventType.CLOCK_UPDATED, payload={"now": NOW.isoformat(), "offset_seconds": 0}, ts=NOW
    )


@pytest.mark.asyncio
async def test_failed_and_unknown_client_do_not_break_multi_client_broadcast() -> None:
    manager = ConnectionManager()
    first, second, failed = Socket(), Socket(), Socket(failed=True)
    for socket in (first, second, failed):
        manager.add(socket)
    manager.remove(Socket())
    await manager.broadcast(clock_event())
    await manager.broadcast(clock_event())
    assert len(first.frames) == len(second.frames) == 2
    assert failed.closed
    await manager.shutdown()
    assert first.closed and second.closed


@pytest.mark.asyncio
async def test_unknown_invalid_and_internal_payload_fields_are_filtered() -> None:
    manager, socket = ConnectionManager(), Socket()
    manager.add(socket)
    dispatcher = EventDispatcher(manager)
    await dispatcher.dispatch('{"type":"unknown","payload":{},"ts":"bad"}')
    await dispatcher.dispatch('{"type":"clock.updated","payload":{},"ts":"bad"}')
    event = clock_event()
    event.payload["phone_e164"] = "+923001234567"
    await dispatcher.dispatch(event.model_dump_json())
    assert len(socket.frames) == 1
    assert "phone" not in socket.frames[0]
    await dispatcher.shutdown()


@pytest.mark.asyncio
async def test_metrics_burst_coalesces_per_campaign_without_delaying_clock() -> None:
    manager, socket = ConnectionManager(), Socket()
    manager.add(socket)
    dispatcher = EventDispatcher(manager, debounce_seconds=0.02)
    campaign_id = str(uuid4())
    event = EventEnvelope(
        type=EventType.METRICS_UPDATED, payload={"campaign_id": campaign_id}, ts=NOW
    )
    for _ in range(3):
        await dispatcher.dispatch(event.model_dump_json())
    await dispatcher.dispatch(clock_event().model_dump_json())
    assert len(socket.frames) == 1
    socket.received.clear()
    await asyncio.wait_for(socket.received.wait(), timeout=1)
    assert len(socket.frames) == 2
    assert EventEnvelope.model_validate_json(socket.frames[-1]).type == EventType.METRICS_UPDATED
    await dispatcher.shutdown()


@pytest.mark.asyncio
async def test_publisher_uses_channel_clock_and_public_envelope() -> None:
    redis = RedisRecorder()
    publisher = RedisEventPublisher(redis, FixedClock(NOW))
    await publisher.publish(
        "clock.updated",
        {
            "now": NOW.isoformat(),
            "offset_seconds": 3,
            "internal_secret": "hidden",
        },
    )
    channel, data = redis.calls[0]
    event = EventEnvelope.model_validate_json(data)
    assert channel == EVENT_CHANNEL
    assert event.ts == NOW
    assert set(event.model_dump()) == {"type", "payload", "ts"}
    assert "hidden" not in data


@pytest.mark.asyncio
async def test_redis_failure_does_not_raise_after_domain_commit() -> None:
    publisher = RedisEventPublisher(RedisRecorder(failed=True), FixedClock(NOW))
    await publisher.publish("clock.updated", clock_event().payload)


@pytest.mark.asyncio
async def test_expired_connection_never_receives_an_event() -> None:
    manager, socket = ConnectionManager(), Socket()
    manager.add(socket, expires_at=clock.now() - timedelta(seconds=1))
    await manager.broadcast(clock_event())
    assert socket.frames == []
    assert socket.closed


@pytest.mark.asyncio
async def test_shutdown_flushes_pending_metrics_and_closes_tasks() -> None:
    manager, socket = ConnectionManager(), Socket()
    manager.add(socket)
    dispatcher = EventDispatcher(manager)
    event = EventEnvelope(type=EventType.METRICS_UPDATED, payload={"campaign_id": None}, ts=NOW)
    await dispatcher.dispatch(event.model_dump_json())
    await dispatcher.shutdown()
    assert len(socket.frames) == 1
    assert not dispatcher._tasks


@pytest.mark.asyncio
async def test_metrics_arriving_during_broadcast_gets_a_fresh_window() -> None:
    class BlockingSocket(Socket):
        def __init__(self) -> None:
            super().__init__()
            self.entered = asyncio.Event()
            self.release = asyncio.Event()

        async def send_text(self, data: str) -> None:
            self.entered.set()
            await self.release.wait()
            await super().send_text(data)

    manager, socket = ConnectionManager(), BlockingSocket()
    manager.add(socket)
    dispatcher = EventDispatcher(manager, debounce_seconds=0)
    event = EventEnvelope(type=EventType.METRICS_UPDATED, payload={"campaign_id": None}, ts=NOW)
    await dispatcher.dispatch(event.model_dump_json())
    await asyncio.wait_for(socket.entered.wait(), timeout=1)
    await dispatcher.dispatch(event.model_dump_json())
    socket.release.set()
    await asyncio.wait_for(asyncio.gather(*tuple(dispatcher._active)), timeout=1)
    await dispatcher.shutdown()
    assert len(socket.frames) == 2
