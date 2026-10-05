"""Demo-clock route authorization and delegation tests."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_demo_clock_service
from app.main import app
from app.models.enums import UserRole
from app.schemas.demo import DemoClockAdvance, DemoClockOut
from app.schemas.user import UserOut

NOW = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)


class StubDemoClockService:
    """Return deterministic clock values and record writes."""

    def __init__(self) -> None:
        self.advanced: DemoClockAdvance | None = None
        self.reset_called = False

    def get(self) -> DemoClockOut:
        return DemoClockOut(now=NOW, offset_seconds=0)

    async def advance(self, request: DemoClockAdvance) -> DemoClockOut:
        self.advanced = request
        return DemoClockOut(now=NOW, offset_seconds=90_000)

    async def reset(self) -> DemoClockOut:
        self.reset_called = True
        return self.get()


def test_admin_can_read_advance_and_reset_clock() -> None:
    service = StubDemoClockService()
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.ADMIN)
    app.dependency_overrides[get_demo_clock_service] = lambda: service
    try:
        client = TestClient(app)
        current = client.get("/api/v1/demo/clock")
        advanced = client.post(
            "/api/v1/demo/clock/actions/advance",
            json={"days": 1, "hours": 1},
        )
        reset = client.post("/api/v1/demo/clock/actions/reset")
    finally:
        app.dependency_overrides.clear()

    assert current.status_code == advanced.status_code == reset.status_code == 200
    assert advanced.json()["offset_seconds"] == 90_000
    assert service.advanced == DemoClockAdvance(days=1, hours=1)
    assert service.reset_called is True


def test_coordinator_can_read_but_cannot_change_clock() -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.COORDINATOR)
    app.dependency_overrides[get_demo_clock_service] = StubDemoClockService
    try:
        client = TestClient(app)
        current = client.get("/api/v1/demo/clock")
        advance = client.post("/api/v1/demo/clock/actions/advance", json={"hours": 1})
        reset = client.post("/api/v1/demo/clock/actions/reset")
    finally:
        app.dependency_overrides.clear()

    assert current.status_code == 200
    assert advance.status_code == reset.status_code == 403


def test_demo_clock_routes_require_authentication() -> None:
    client = TestClient(app)

    assert client.get("/api/v1/demo/clock").status_code == 401
    assert client.post("/api/v1/demo/clock/actions/advance", json={}).status_code == 401


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(),
        email=f"clock-{role.value}@example.test",
        full_name=role.value.title(),
        role=role,
        is_active=True,
    )
