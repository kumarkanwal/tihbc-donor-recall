"""Tests for the demo clock."""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.clock import Clock


class FakeClockPersistence:
    """In-memory persistence double for clock unit tests."""

    def __init__(self, offset_seconds: int = 0) -> None:
        self.offset_seconds = offset_seconds
        self.load_calls = 0

    async def load_offset_seconds(self) -> int:
        self.load_calls += 1
        return self.offset_seconds

    async def increment_offset_seconds(self, seconds: int) -> int:
        self.offset_seconds += seconds
        return self.offset_seconds

    async def set_offset_seconds(self, seconds: int) -> int:
        self.offset_seconds = seconds
        return self.offset_seconds


@pytest.mark.asyncio
async def test_clock_loads_advances_and_resets_persisted_offset() -> None:
    persistence = FakeClockPersistence(offset_seconds=3600)
    test_clock = Clock()
    before = datetime.now(UTC)
    await test_clock.initialize(persistence)

    assert test_clock.offset == timedelta(hours=1)
    assert test_clock.now() >= before + timedelta(hours=1)
    assert persistence.load_calls == 1

    advanced = await test_clock.advance(timedelta(days=3, hours=2))

    expected_offset = timedelta(days=3, hours=3)
    assert advanced >= before + expected_offset
    assert test_clock.offset == expected_offset
    assert persistence.offset_seconds == int(expected_offset.total_seconds())

    reset = await test_clock.reset()

    assert test_clock.offset == timedelta()
    assert persistence.offset_seconds == 0
    assert before <= reset <= datetime.now(UTC)
    assert persistence.load_calls == 1


@pytest.mark.asyncio
async def test_clock_rejects_invalid_advances() -> None:
    test_clock = Clock()
    await test_clock.initialize(FakeClockPersistence())

    with pytest.raises(ValueError, match="negative"):
        await test_clock.advance(timedelta(seconds=-1))

    with pytest.raises(ValueError, match="whole seconds"):
        await test_clock.advance(timedelta(microseconds=1))


@pytest.mark.asyncio
async def test_clock_requires_persistence_before_changes() -> None:
    test_clock = Clock()

    with pytest.raises(RuntimeError, match="not initialized"):
        await test_clock.reset()
