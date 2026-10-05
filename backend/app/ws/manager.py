"""Per-process connection ownership and isolated broadcasts."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

import structlog

from app.core.clock import wall_clock_now
from app.ws.events import EventEnvelope

SEND_TIMEOUT_SECONDS = 5.0
logger = structlog.get_logger(__name__)


class ClientSocket(Protocol):
    """Capabilities used by the connection manager."""

    async def send_text(self, data: str) -> None:
        """Send one public event."""

    async def close(self, code: int = 1000) -> None:
        """Close the transport."""


@dataclass
class Connection:
    """Serialize sends to one client."""

    socket: ClientSocket
    expires_at: datetime | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class ConnectionManager:
    """Own active sockets for one API process."""

    def __init__(self) -> None:
        self._connections: dict[int, Connection] = {}

    def add(self, socket: ClientSocket, *, expires_at: datetime | None = None) -> None:
        """Register an already accepted socket."""
        self._connections[id(socket)] = Connection(socket, expires_at)

    def remove(self, socket: ClientSocket) -> None:
        """Discard disconnected or unknown sockets safely."""
        self._connections.pop(id(socket), None)

    async def broadcast(self, event: EventEnvelope) -> None:
        """Broadcast concurrently; isolate failed or slow clients."""
        data = event.public().model_dump_json()
        await asyncio.gather(
            *(self._send(connection, data) for connection in tuple(self._connections.values()))
        )

    async def _send(self, connection: Connection, data: str) -> None:
        if connection.expires_at is not None and wall_clock_now() >= connection.expires_at:
            self.remove(connection.socket)
            await self._close(connection.socket, code=1008)
            return
        try:
            async with asyncio.timeout(SEND_TIMEOUT_SECONDS):
                async with connection.lock:
                    await connection.socket.send_text(data)
        except Exception as error:
            logger.warning("websocket_send_failed", error_type=type(error).__name__)
            self.remove(connection.socket)
            await self._close(connection.socket)

    async def shutdown(self) -> None:
        """Close remaining connections at application shutdown."""
        sockets = tuple(item.socket for item in self._connections.values())
        self._connections.clear()
        await asyncio.gather(*(self._close(socket) for socket in sockets))

    @staticmethod
    async def _close(socket: ClientSocket, *, code: int = 1001) -> None:
        try:
            async with asyncio.timeout(SEND_TIMEOUT_SECONDS):
                await socket.close(code=code)
        except Exception as error:
            logger.debug("websocket_close_failed", error_type=type(error).__name__)
