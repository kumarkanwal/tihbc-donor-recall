"""Tests for authentication business rules."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.core.clock import Clock
from app.core.errors import UnauthorizedError
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest
from app.services.auth_service import INVALID_CREDENTIALS_MESSAGE, AuthService

PASSWORD = "CorrectPassword123!"
JWT_TEST_SECRET = SecretStr("test-jwt-secret-with-at-least-32-bytes")


def _user(*, active: bool = True) -> User:
    return User(
        id=uuid4(),
        email="admin@tihbc.demo",
        full_name="TIHBC Admin",
        password_hash=hash_password(PASSWORD),
        role=UserRole.ADMIN,
        is_active=active,
    )


def _service(repository: UserRepository) -> AuthService:
    return AuthService(
        repository,
        jwt_secret=JWT_TEST_SECRET,
        jwt_expires_minutes=30,
        current_clock=Clock(),
    )


@pytest.mark.asyncio
async def test_authenticate_success_normalizes_email() -> None:
    user = _user()
    repository = Mock(spec=UserRepository)
    repository.get_by_email = AsyncMock(return_value=user)

    response = await _service(repository).authenticate(
        LoginRequest(email="  ADMIN@TIHBC.DEMO ", password=PASSWORD)
    )

    repository.get_by_email.assert_awaited_once_with("admin@tihbc.demo")
    assert response.token_type == "bearer"
    assert response.access_token
    assert response.user.id == user.id
    assert "password" not in response.user.model_dump()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user", "password"),
    [
        (_user(), "WrongPassword123!"),
        (None, PASSWORD),
        (_user(active=False), PASSWORD),
    ],
    ids=["wrong-password", "unknown-email", "inactive-user"],
)
async def test_authenticate_rejects_with_same_generic_error(
    user: User | None, password: str
) -> None:
    repository = Mock(spec=UserRepository)
    repository.get_by_email = AsyncMock(return_value=user)

    with pytest.raises(UnauthorizedError) as error:
        await _service(repository).authenticate(
            LoginRequest(email="person@example.test", password=password)
        )

    assert error.value.message == INVALID_CREDENTIALS_MESSAGE


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token() -> None:
    repository = Mock(spec=UserRepository)
    repository.get = AsyncMock()

    with pytest.raises(UnauthorizedError):
        await _service(repository).get_current_user("not-a-token")

    repository.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_returns_active_database_user() -> None:
    user = _user()
    repository = Mock(spec=UserRepository)
    repository.get_by_email = AsyncMock(return_value=user)
    repository.get = AsyncMock(return_value=user)
    service = _service(repository)
    response = await service.authenticate(LoginRequest(email=user.email, password=PASSWORD))

    current_user = await service.get_current_user(response.access_token)

    repository.get.assert_awaited_once_with(user.id)
    assert current_user.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_database_user() -> None:
    user = _user()
    repository = Mock(spec=UserRepository)
    repository.get_by_email = AsyncMock(return_value=user)
    repository.get = AsyncMock(
        return_value=User(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            password_hash=user.password_hash,
            role=user.role,
            is_active=False,
        )
    )
    service = _service(repository)
    response = await service.authenticate(LoginRequest(email=user.email, password=PASSWORD))

    with pytest.raises(UnauthorizedError):
        await service.get_current_user(response.access_token)
