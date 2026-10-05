"""Demo-clock reads and administrator time controls."""

from datetime import timedelta
from typing import Protocol

from app.core.clock import Clock
from app.core.errors import ForbiddenError
from app.scheduler.tick import TickSummary
from app.schemas.demo import DemoClockAdvance, DemoClockOut
from app.services.events.base import EventPublisher
from app.services.events.types import EventType


class TickRunner(Protocol):
    """Scheduler capability required by demo-clock advances."""

    async def run(self) -> TickSummary:
        """Run one immediate scheduler tick."""


class DemoClockService:
    """Persist clock controls, trigger ticks, and publish committed changes."""

    def __init__(
        self,
        current_clock: Clock,
        tick: TickRunner,
        publisher: EventPublisher,
        *,
        demo_mode: bool,
    ) -> None:
        self._clock = current_clock
        self._tick = tick
        self._publisher = publisher
        self._demo_mode = demo_mode

    def get(self) -> DemoClockOut:
        """Return the current cached demo time and offset."""
        return self._snapshot()

    async def advance(self, request: DemoClockAdvance) -> DemoClockOut:
        """Advance the durable offset and immediately run one scheduler tick."""
        self._require_demo_mode()
        await self._clock.advance(timedelta(days=request.days, hours=request.hours))
        await self._tick.run()
        result = self._snapshot()
        await self._publish(result)
        return result

    async def reset(self) -> DemoClockOut:
        """Reset the durable offset to zero."""
        self._require_demo_mode()
        await self._clock.reset()
        result = self._snapshot()
        await self._publish(result)
        return result

    def _snapshot(self) -> DemoClockOut:
        return DemoClockOut(
            now=self._clock.now(),
            offset_seconds=int(self._clock.offset.total_seconds()),
        )

    async def _publish(self, result: DemoClockOut) -> None:
        await self._publisher.publish(
            EventType.CLOCK_UPDATED.value,
            result.model_dump(mode="json"),
        )

    def _require_demo_mode(self) -> None:
        if not self._demo_mode:
            raise ForbiddenError("Demo clock changes are disabled")
