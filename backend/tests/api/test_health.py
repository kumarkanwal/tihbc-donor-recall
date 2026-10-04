"""Tests for unauthenticated health probes."""

from collections.abc import AsyncIterator, Callable

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.redis import get_redis
from app.main import app


class FakeDatabaseSession:
    """Controllable database session readiness stub."""

    def __init__(self, *, available: bool) -> None:
        self.available = available

    async def execute(self, statement: object) -> None:
        del statement
        if not self.available:
            raise ConnectionError("database unavailable")


class FakeRedis:
    """Controllable Redis readiness stub."""

    def __init__(self, *, available: bool) -> None:
        self.available = available

    async def ping(self) -> bool:
        if not self.available:
            raise ConnectionError("redis unavailable")
        return True


def _override_db(*, available: bool) -> Callable[[], AsyncIterator[FakeDatabaseSession]]:
    async def dependency() -> AsyncIterator[FakeDatabaseSession]:
        yield FakeDatabaseSession(available=available)

    return dependency


def _override_redis(*, available: bool) -> Callable[[], FakeRedis]:
    def dependency() -> FakeRedis:
        return FakeRedis(available=available)

    return dependency


def test_live_is_always_healthy() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_database_and_redis_are_available() -> None:
    app.dependency_overrides[get_db] = _override_db(available=True)
    app.dependency_overrides[get_redis] = _override_redis(available=True)
    try:
        response = TestClient(app).get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "redis": "ok"},
    }


def test_ready_reports_all_failed_dependencies() -> None:
    app.dependency_overrides[get_db] = _override_db(available=False)
    app.dependency_overrides[get_redis] = _override_redis(available=False)
    try:
        response = TestClient(app).get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "details": {"failed": ["database", "redis"]},
    }
