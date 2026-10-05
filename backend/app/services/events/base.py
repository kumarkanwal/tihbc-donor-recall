"""Domain event publisher contract."""

from collections.abc import Mapping
from typing import Protocol


class EventPublisher(Protocol):
    """Publish committed domain changes to an external fan-out layer."""

    async def publish(self, event_type: str, payload: Mapping[str, object]) -> None:
        """Publish one event after its database transaction commits."""
