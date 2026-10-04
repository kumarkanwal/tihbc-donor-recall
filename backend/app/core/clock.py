"""UTC demo clock used by all backend time-dependent behavior."""

from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Protocol


class ClockPersistence(Protocol):
    """Persistence operations required by the demo clock."""

    async def load_offset_seconds(self) -> int:
        """Load the current offset in whole seconds."""

    async def increment_offset_seconds(self, seconds: int) -> int:
        """Atomically increment and return the offset."""

    async def set_offset_seconds(self, seconds: int) -> int:
        """Replace and return the offset."""


class Clock:
    """Provide fast cached time with durable offset changes."""

    def __init__(self) -> None:
        self._offset = timedelta()
        self._lock = Lock()
        self._persistence: ClockPersistence | None = None

    async def initialize(self, persistence: ClockPersistence) -> None:
        """Load the persisted offset and bind persistence for future changes."""
        offset_seconds = await persistence.load_offset_seconds()
        with self._lock:
            self._persistence = persistence
            self._offset = timedelta(seconds=offset_seconds)

    def now(self) -> datetime:
        """Return the timezone-aware current demo time in UTC."""
        with self._lock:
            offset = self._offset
        return datetime.now(UTC) + offset

    @property
    def offset(self) -> timedelta:
        """Return the current demo offset."""
        with self._lock:
            return self._offset

    async def advance(self, delta: timedelta) -> datetime:
        """Persist and cache a non-negative whole-second advance."""
        if delta < timedelta():
            raise ValueError("Clock cannot be advanced by a negative duration")
        total_seconds = delta.total_seconds()
        if not total_seconds.is_integer():
            raise ValueError("Clock can only be advanced by whole seconds")
        persistence = self._require_persistence()
        offset_seconds = await persistence.increment_offset_seconds(int(total_seconds))
        with self._lock:
            self._offset = timedelta(seconds=offset_seconds)
        return self.now()

    async def reset(self) -> datetime:
        """Persist and cache a zero offset."""
        persistence = self._require_persistence()
        await persistence.set_offset_seconds(0)
        with self._lock:
            self._offset = timedelta()
        return self.now()

    def _require_persistence(self) -> ClockPersistence:
        with self._lock:
            persistence = self._persistence
        if persistence is None:
            raise RuntimeError("Clock persistence is not initialized")
        return persistence


clock = Clock()


def get_clock() -> Clock:
    """Return the process-wide demo clock."""
    return clock
