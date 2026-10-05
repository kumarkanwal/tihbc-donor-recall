"""The real WebSocket authenticator validates current database users."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
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
from app.core.security import create_access_token
from app.main import create_app
from app.models.enums import UserRole


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
        current_clock=clock,
    )
    socket = WebSocket({"type": "websocket", "app": application}, AsyncMock(), AsyncMock())
    with pytest.raises(UnauthorizedError):
        await authenticate_socket(socket, token)
    user_lookup.assert_awaited_once()
