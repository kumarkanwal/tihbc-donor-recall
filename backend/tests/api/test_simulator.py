"""Simulator authentication, staff write access, and reply validation."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.simulator_deps import (
    get_simulator_query_service,
    get_simulator_receipt_service,
    get_simulator_reply_service,
)
from app.main import app
from app.models.enums import UserRole
from app.schemas.simulator import (
    ConversationPage,
    MessagePage,
    OpenConversationResult,
    SimulatorMessage,
)
from app.schemas.user import UserOut
from app.services.messaging.payloads import message_created_payload
from tests.services.simulator_fixtures import reply_service


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.COORDINATOR])
def test_both_staff_roles_can_browse_and_open_conversations(role: UserRole) -> None:
    query, receipts = AsyncMock(), AsyncMock()
    query.conversations.return_value = ConversationPage(items=[], total=0, page=1, page_size=20)
    query.messages.return_value = MessagePage(items=[], next_before=None, limit=50)
    receipts.open.return_value = OpenConversationResult(read_count=0)
    app.dependency_overrides[get_current_user] = lambda: _user(role)
    app.dependency_overrides[get_simulator_query_service] = lambda: query
    app.dependency_overrides[get_simulator_receipt_service] = lambda: receipts
    try:
        client = TestClient(app)
        assert client.get("/api/v1/simulator/conversations").status_code == 200
        path = f"/api/v1/simulator/conversations/{uuid4()}"
        assert client.get(f"{path}/messages").status_code == 200
        assert client.post(f"{path}/actions/open").status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "body",
    [
        {"type": "text", "text": "  "},
        {"type": "button", "button_id": "confirm"},
        {"type": "invalid", "text": "Hi"},
        {"type": "text", "text": "a" * 4097},
    ],
)
def test_reply_shapes_are_validated_without_echoing_input(body: dict[str, str]) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.COORDINATOR)
    app.dependency_overrides[get_simulator_reply_service] = AsyncMock
    try:
        response = TestClient(app).post(
            f"/api/v1/simulator/conversations/{uuid4()}/replies", json=body
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422
    assert "input" not in str(response.json())


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.COORDINATOR])
def test_both_staff_roles_can_submit_replies(role: UserRole) -> None:
    fixture = reply_service()
    replies = AsyncMock()
    replies.reply.return_value = SimulatorMessage.model_validate(
        message_created_payload(fixture.source)
    )
    app.dependency_overrides[get_current_user] = lambda: _user(role)
    app.dependency_overrides[get_simulator_reply_service] = lambda: replies
    try:
        response = TestClient(app).post(
            f"/api/v1/simulator/conversations/{fixture.person.id}/replies",
            json={"type": "text", "text": "Hello"},
        )
        assert response.status_code == 201
        assert replies.reply.await_args.args[1].text == "Hello"
    finally:
        app.dependency_overrides.clear()


def test_simulator_requires_authentication() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/simulator/conversations").status_code == 401
    assert (
        client.post(
            f"/api/v1/simulator/conversations/{uuid4()}/replies",
            json={"type": "text", "text": "Hello"},
        ).status_code
        == 401
    )


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(), email="staff@example.test", full_name="Staff", role=role, is_active=True
    )
