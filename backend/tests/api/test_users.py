"""API tests for active-user lookup."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_user_service
from app.main import app
from app.models.enums import UserRole
from app.schemas.user import UserOut, UserPage


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(),
        email=f"{role.value}@tihbc.demo",
        full_name=f"TIHBC {role.value.title()}",
        role=role,
        is_active=True,
    )


class FakeUserService:
    """Capture list filters for route tests."""

    def __init__(self, result: UserOut) -> None:
        self.result = result
        self.received: tuple[UserRole | None, int, int] | None = None

    async def list_active(
        self,
        *,
        role: UserRole | None,
        page: int,
        page_size: int,
    ) -> UserPage:
        self.received = (role, page, page_size)
        return UserPage(items=[self.result], total=1, page=page, page_size=page_size)


def test_users_allows_coordinator_and_forwards_role_filter() -> None:
    coordinator = _user(UserRole.COORDINATOR)
    result = _user(UserRole.ADMIN)
    service = FakeUserService(result)
    app.dependency_overrides[get_current_user] = lambda: coordinator
    app.dependency_overrides[get_user_service] = lambda: service
    try:
        response = TestClient(app).get("/api/v1/users?role=admin&page=2&page_size=10")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["role"] == "admin"
    assert service.received == (UserRole.ADMIN, 2, 10)


def test_users_requires_authentication() -> None:
    response = TestClient(app).get("/api/v1/users")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
