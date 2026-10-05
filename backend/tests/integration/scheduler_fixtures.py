"""Test doubles and composition helpers for scheduler integration coverage."""

import asyncio
from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import Clock, ClockPersistence
from app.core.config import Settings
from app.messaging.base import OutboundButton, ProviderSendResult
from app.models.enums import MediaType
from app.scheduler.tick import SchedulerTick
from tests.integration.messaging_fixtures import RecordingProvider


class StaticClockPersistence:
    """Leave a fixed test clock unchanged when a tick reloads its offset."""

    async def load_offset_seconds(self) -> int:
        return 0

    async def increment_offset_seconds(self, seconds: int) -> int:
        return seconds

    async def set_offset_seconds(self, seconds: int) -> int:
        return seconds


class MutableClockPersistence:
    """Expose mutable persisted offsets and count worker reloads."""

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


class CollectingPublisher:
    """Collect domain events across scheduler-owned sessions."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Mapping[str, object]]] = []

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        self.events.append((event_type, payload))


class FailFirstProvider(RecordingProvider):
    """Fail the first interactive send and accept later sends."""

    def __init__(self) -> None:
        super().__init__()
        self.failed = False

    async def send_interactive_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        buttons: tuple[OutboundButton, ...],
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        if not self.failed:
            self.failed = True
            raise RuntimeError("simulated provider failure")
        return await super().send_interactive_message(
            message_id=message_id,
            recipient=recipient,
            body=body,
            buttons=buttons,
            media_type=media_type,
            media_url=media_url,
        )


class BlockingProvider(RecordingProvider):
    """Hold the first send while a concurrent tick attempts the same row."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def send_interactive_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        buttons: tuple[OutboundButton, ...],
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        self.entered.set()
        await self.release.wait()
        return await super().send_interactive_message(
            message_id=message_id,
            recipient=recipient,
            body=body,
            buttons=buttons,
            media_type=media_type,
            media_url=media_url,
        )


def build_test_tick(
    session_factory: async_sessionmaker[AsyncSession],
    current_clock: Clock,
    provider: RecordingProvider,
    publisher: CollectingPublisher | None = None,
    clock_persistence: ClockPersistence | None = None,
) -> SchedulerTick:
    """Build a tick with deterministic in-memory external dependencies."""
    return SchedulerTick(
        session_factory,
        Settings(),
        current_clock,
        clock_persistence or StaticClockPersistence(),
        provider,
        publisher or CollectingPublisher(),
    )
