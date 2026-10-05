"""Tests for demo-clock controls and immediate tick execution."""

from collections.abc import Mapping

import pytest

from app.core.clock import Clock
from app.core.errors import ForbiddenError
from app.scheduler.tick import TickSummary
from app.schemas.demo import DemoClockAdvance
from app.services.demo_clock import DemoClockService
from tests.core.test_clock import FakeClockPersistence


class RecordingTick:
    """Count immediate scheduler runs."""

    def __init__(self) -> None:
        self.calls = 0

    async def run(self) -> TickSummary:
        self.calls += 1
        return TickSummary()


class RecordingPublisher:
    """Capture clock events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Mapping[str, object]]] = []

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        self.events.append((event_type, payload))


@pytest.mark.asyncio
async def test_advance_persists_offset_runs_tick_and_publishes() -> None:
    current_clock = Clock()
    persistence = FakeClockPersistence()
    await current_clock.initialize(persistence)
    tick = RecordingTick()
    publisher = RecordingPublisher()
    service = DemoClockService(current_clock, tick, publisher, demo_mode=True)

    result = await service.advance(DemoClockAdvance(days=3, hours=2))

    assert result.offset_seconds == 266_400
    assert persistence.offset_seconds == 266_400
    assert tick.calls == 1
    assert publisher.events == [("clock.updated", result.model_dump(mode="json"))]


@pytest.mark.asyncio
async def test_reset_does_not_run_tick() -> None:
    current_clock = Clock()
    persistence = FakeClockPersistence(offset_seconds=3600)
    await current_clock.initialize(persistence)
    tick = RecordingTick()
    service = DemoClockService(
        current_clock,
        tick,
        RecordingPublisher(),
        demo_mode=True,
    )

    result = await service.reset()

    assert result.offset_seconds == 0
    assert tick.calls == 0


@pytest.mark.asyncio
async def test_clock_writes_are_disabled_outside_demo_mode() -> None:
    current_clock = Clock()
    await current_clock.initialize(FakeClockPersistence())
    tick = RecordingTick()
    service = DemoClockService(
        current_clock,
        tick,
        RecordingPublisher(),
        demo_mode=False,
    )

    with pytest.raises(ForbiddenError, match="disabled"):
        await service.advance(DemoClockAdvance(hours=1))
    with pytest.raises(ForbiddenError, match="disabled"):
        await service.reset()

    assert tick.calls == 0
