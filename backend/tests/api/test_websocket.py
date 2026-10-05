"""WebSocket authentication and connection lifetime checks."""

from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.websockets import WebSocketDisconnect

from app.core.clock import clock
from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import InvalidAccessTokenError, create_access_token, verify_access_token
from app.main import create_app
from app.models.enums import UserRole
from app.ws.manager import ConnectionManager


@pytest.mark.parametrize("token", [None, "invalid", "expired"])
def test_missing_invalid_and_expired_tokens_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    token: str | None,
) -> None:
    settings = get_settings()
    settings = settings.model_copy(update={"jwt_secret": SecretStr("test-secret-" * 4)})
    if token == "expired":
        with monkeypatch.context() as patch:
            patch.setattr(
                "app.core.security.wall_clock_now", lambda: clock.now() - timedelta(hours=1)
            )
            token = create_access_token(
                user_id=uuid4(),
                role=UserRole.ADMIN,
                secret=settings.jwt_secret,
                expires_minutes=1,
            )

    async def authenticate(socket: object, value: str) -> None:
        del socket
        try:
            verify_access_token(value, secret=settings.jwt_secret)
        except InvalidAccessTokenError:
            raise UnauthorizedError() from None

    monkeypatch.setattr("app.api.websocket.authenticate_socket", authenticate)
    client = TestClient(create_app())
    path = "/ws" if token is None else f"/ws?token={token}"
    with pytest.raises(WebSocketDisconnect) as error, client.websocket_connect(path):
        pass
    assert error.value.code == 1008


def test_accepted_socket_revalidates_and_disconnects_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authenticate = AsyncMock(return_value=clock.now() + timedelta(hours=1))
    monkeypatch.setattr("app.api.websocket.authenticate_socket", authenticate)
    application = create_app()
    manager = ConnectionManager()
    application.state.ws_manager = manager
    with TestClient(application).websocket_connect("/ws?token=accepted") as socket:
        socket.send_text("ignored client action")
    assert authenticate.await_count >= 1
    assert not manager._connections


def test_expiry_during_connection_closes_with_policy_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authenticate = AsyncMock(side_effect=[clock.now() + timedelta(hours=1), UnauthorizedError()])
    monkeypatch.setattr("app.api.websocket.authenticate_socket", authenticate)
    monkeypatch.setattr("app.api.websocket.AUTH_REFRESH_SECONDS", 0.001)
    application = create_app()
    application.state.ws_manager = ConnectionManager()
    with (
        TestClient(application).websocket_connect("/ws?token=accepted") as socket,
        pytest.raises(WebSocketDisconnect) as error,
    ):
        socket.receive_json()
    assert error.value.code == 1008
