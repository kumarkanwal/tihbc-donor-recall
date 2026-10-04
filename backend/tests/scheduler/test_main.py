"""Tests for the placeholder scheduler lifecycle."""

import asyncio

import pytest
from structlog.testing import capture_logs

from app.scheduler.__main__ import heartbeat_loop


@pytest.mark.asyncio
async def test_heartbeat_loop_logs_lifecycle_and_stops_cleanly() -> None:
    shutdown_event = asyncio.Event()

    with capture_logs() as logs:
        worker = asyncio.create_task(heartbeat_loop(60, shutdown_event))
        await asyncio.sleep(0)
        shutdown_event.set()
        await worker

    events = [entry["event"] for entry in logs]
    assert events == ["scheduler_started", "scheduler_heartbeat", "scheduler_stopped"]
