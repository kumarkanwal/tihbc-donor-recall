"""Real Redis transport from a worker publisher to accepted WebSocket clients."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.clock import clock
from app.core.config import get_settings
from app.core.redis import create_redis_client
from app.main import create_app
from app.services.events.redis import RedisEventPublisher
from app.ws.events import EventType
from app.ws.manager import ConnectionManager
from app.ws.subscriber import EventDispatcher, RedisEventSubscriber

pytestmark = pytest.mark.redis


def test_worker_published_event_reaches_multiple_clients_through_real_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    channel = f"tihbc:test:{uuid4()}"
    settings = get_settings()
    monkeypatch.setattr(
        "app.api.websocket.authenticate_socket",
        AsyncMock(return_value=clock.now() + timedelta(hours=1)),
    )
    application = create_app()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        redis = create_redis_client(settings.redis_url)
        manager = ConnectionManager()
        app.state.ws_manager = manager
        subscriber = RedisEventSubscriber(redis, EventDispatcher(manager), channel=channel)
        await subscriber.start()
        try:
            await asyncio.wait_for(subscriber.ready.wait(), timeout=5)
            yield
        finally:
            await subscriber.stop()
            await manager.shutdown()
            await redis.aclose()

    application.router.lifespan_context = lifespan

    async def worker_publish() -> None:
        # Independent connection models a separate worker process.
        redis = create_redis_client(settings.redis_url)
        try:
            publisher = RedisEventPublisher(redis, clock, channel=channel)
            await publisher.publish(
                EventType.CLOCK_UPDATED.value, {"now": clock.now().isoformat(), "offset_seconds": 0}
            )
        finally:
            await redis.aclose()

    with (
        TestClient(application) as client,
        client.websocket_connect("/ws?token=accepted") as first,
        client.websocket_connect("/ws?token=accepted") as second,
    ):
        assert client.portal is not None
        client.portal.call(worker_publish)
        assert first.receive_json()["type"] == second.receive_json()["type"] == "clock.updated"
