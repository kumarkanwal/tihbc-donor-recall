"""Tests for the scheduler worker loop."""

import asyncio
from dataclasses import dataclass

import pytest
from structlog.testing import capture_logs

from app.scheduler.__main__ import dispatcher_loop
from app.scheduler.tick import TickSummary


@dataclass
class StoppingTick:
    """Stop the loop after one successful tick."""

    shutdown: asyncio.Event
    calls: int = 0

    async def run(self) -> TickSummary:
        self.calls += 1
        self.shutdown.set()
        return TickSummary()


@dataclass
class RecoveringTick:
    """Fail once, then prove the loop keeps polling."""

    shutdown: asyncio.Event
    calls: int = 0

    async def run(self) -> TickSummary:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("tick failed")
        self.shutdown.set()
        return TickSummary()


@pytest.mark.asyncio
async def test_dispatcher_runs_immediately_and_stops_cleanly() -> None:
    shutdown = asyncio.Event()
    tick = StoppingTick(shutdown)

    with capture_logs() as logs:
        await dispatcher_loop(tick, 60, shutdown)

    assert tick.calls == 1
    assert [entry["event"] for entry in logs] == ["scheduler_started", "scheduler_stopped"]


@pytest.mark.asyncio
async def test_dispatcher_continues_after_tick_failure() -> None:
    shutdown = asyncio.Event()
    tick = RecoveringTick(shutdown)

    with capture_logs() as logs:
        await dispatcher_loop(tick, 0.001, shutdown)

    assert tick.calls == 2
    assert "scheduler_tick_failed" in {entry["event"] for entry in logs}
