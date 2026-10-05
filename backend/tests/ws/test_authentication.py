"""The real WebSocket authenticator validates current database users."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import WebSocket
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.websocket import authenticate_socket
from app.core.clock import clock
from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.enums import UserRole
from app.models.user import User


@pytest.mark.asyncio
async def test_valid_token_still_requires_an_active_database_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings().model_copy(update={"jwt_secret": SecretStr("socket-secret-" * 4)})
    application = create_app(settings)
    session = AsyncMock(spec=AsyncSession)

    @asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        yield session

    application.state.database = SimpleNamespace(session_factory=session_factory)
    user_lookup = AsyncMock(return_value=None)
    monkeypatch.setattr("app.repositories.user.UserRepository.get", user_lookup)
    token = create_access_token(
        user_id=uuid4(),
        role=UserRole.ADMIN,
        secret=settings.jwt_secret,
        expires_minutes=60,
    )
    socket = WebSocket({"type": "websocket", "app": application}, AsyncMock(), AsyncMock())
    with pytest.raises(UnauthorizedError):
        await authenticate_socket(socket, token)
    user_lookup.assert_awaited_once()


@pytest.mark.asyncio
async def test_demo_clock_advance_does_not_reject_websocket_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = get_settings().model_copy(update={"jwt_secret": SecretStr("socket-secret-" * 4)})
    application = create_app(settings)
    session = AsyncMock(spec=AsyncSession)

    @asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        yield session

    user = User(
        id=uuid4(),
        email="admin@example.test",
        full_name="Admin User",
        password_hash=hash_password("StrongPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    application.state.database = SimpleNamespace(session_factory=session_factory)
    monkeypatch.setattr("app.repositories.user.UserRepository.get", AsyncMock(return_value=user))
    token = create_access_token(
        user_id=user.id,
        role=user.role,
        secret=settings.jwt_secret,
        expires_minutes=60,
    )
    real_demo_now = clock.now()
    monkeypatch.setattr(clock, "now", lambda: real_demo_now + timedelta(days=7))
    socket = WebSocket({"type": "websocket", "app": application}, AsyncMock(), AsyncMock())

    expires_at = await authenticate_socket(socket, token)

    assert expires_at > real_demo_now
