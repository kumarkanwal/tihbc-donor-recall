"""API tests for login and current-user routes."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.core.errors import UnauthorizedError
from app.main import app
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut


def _user() -> UserOut:
    return UserOut(
        id=uuid4(),
        email="admin@tihbc.demo",
        full_name="TIHBC Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )


class FakeAuthService:
    """Controllable authentication service for route tests."""

    def __init__(self, user: UserOut) -> None:
        self.user = user

    async def authenticate(self, request: LoginRequest) -> TokenResponse:
        assert request.password.get_secret_value() == "Password123!"
        return TokenResponse(access_token="valid-token", user=self.user)

    async def get_current_user(self, token: str) -> UserOut:
        if token in {"invalid-token", "expired-token"}:
            raise UnauthorizedError("Invalid or expired access token")
        return self.user


def test_login_success() -> None:
    user = _user()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService(user)
    try:
        response = TestClient(app).post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "Password123!"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "valid-token",
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": "admin",
            "is_active": True,
        },
    }


def test_me_accepts_valid_token() -> None:
    user = _user()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService(user)
    try:
        response = TestClient(app).get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)


def test_me_rejects_missing_token_with_documented_shape() -> None:
    response = TestClient(app).get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_rejects_invalid_and_expired_tokens() -> None:
    user = _user()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService(user)
    try:
        for token in ("invalid-token", "expired-token"):
            response = TestClient(app).get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "UNAUTHORIZED"
    finally:
        app.dependency_overrides.clear()
