"""Authenticated, server-only WebSocket transport."""

import asyncio
from datetime import datetime
from typing import cast
from uuid import uuid4

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.clock import clock
from app.core.config import Settings
from app.core.db import DatabaseResources
from app.core.errors import UnauthorizedError
from app.core.security import InvalidAccessTokenError, verify_access_token
from app.repositories.user import UserRepository
from app.services.auth_service import AuthService
from app.ws.manager import ConnectionManager

router = APIRouter()
AUTH_REFRESH_SECONDS = 20.0


async def authenticate_socket(socket: WebSocket, token: str) -> datetime:
    """Resolve the active user and token expiry in a short session."""
    settings = cast(Settings, socket.app.state.settings)
    try:
        claims = verify_access_token(token, secret=settings.jwt_secret, current_clock=clock)
    except InvalidAccessTokenError:
        raise UnauthorizedError() from None
    resources = cast(DatabaseResources, socket.app.state.database)
    async with resources.session_factory() as session:
        service = AuthService(
            UserRepository(session),
            jwt_secret=settings.jwt_secret,
            jwt_expires_minutes=settings.jwt_expires_minutes,
            current_clock=clock,
        )
        await service.get_current_user(token)
        return claims.expires_at


@router.websocket("/ws")
async def websocket_events(socket: WebSocket) -> None:
    """Accept staff and maintain a periodically revalidated connection."""
    token = socket.query_params.get("token")
    structlog.contextvars.bind_contextvars(request_id=str(uuid4()))
    try:
        if not token:
            raise UnauthorizedError()
        expires_at = await authenticate_socket(socket, token)
    except UnauthorizedError:
        await socket.close(code=1008)
        return
    manager = cast(ConnectionManager, socket.app.state.ws_manager)
    await socket.accept()
    manager.add(socket, expires_at=expires_at)
    try:
        while True:
            try:
                async with asyncio.timeout(AUTH_REFRESH_SECONDS):
                    incoming = await socket.receive()
                if incoming["type"] == "websocket.disconnect":
                    break
            except TimeoutError:
                pass
            await authenticate_socket(socket, token)
    except UnauthorizedError:
        await socket.close(code=1008)
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(socket)
