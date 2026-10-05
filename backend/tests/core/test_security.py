"""Tests for password and access-token security primitives."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.core.clock import Clock
from app.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
)
from app.models.enums import UserRole

JWT_TEST_SECRET = SecretStr("test-jwt-secret-with-at-least-32-bytes")


class FakeClockPersistence:
    """In-memory persistence for demo-clock security tests."""

    def __init__(self) -> None:
        self.offset_seconds = 0

    async def load_offset_seconds(self) -> int:
        return self.offset_seconds

    async def increment_offset_seconds(self, seconds: int) -> int:
        self.offset_seconds += seconds
        return self.offset_seconds

    async def set_offset_seconds(self, seconds: int) -> int:
        self.offset_seconds = seconds
        return self.offset_seconds


def test_password_hashing_and_verification() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)
    assert not verify_password("password", "not-an-argon2-hash")


@pytest.mark.asyncio
async def test_demo_clock_advance_does_not_expire_token() -> None:
    test_clock = Clock()
    await test_clock.initialize(FakeClockPersistence())
    user_id = uuid4()
    secret = JWT_TEST_SECRET
    token = create_access_token(
        user_id=user_id,
        role=UserRole.ADMIN,
        secret=secret,
        expires_minutes=5,
    )

    claims = verify_access_token(token, secret=secret)

    assert claims.user_id == user_id
    assert claims.role == UserRole.ADMIN
    assert claims.expires_at - claims.issued_at == timedelta(minutes=5)

    await test_clock.advance(timedelta(days=7))

    assert verify_access_token(token, secret=secret).user_id == user_id


def test_token_expires_against_wall_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    issued_at = datetime(2026, 10, 5, 12, tzinfo=UTC)
    monkeypatch.setattr("app.core.security.wall_clock_now", lambda: issued_at)
    token = create_access_token(
        user_id=uuid4(),
        role=UserRole.ADMIN,
        secret=JWT_TEST_SECRET,
        expires_minutes=5,
    )
    monkeypatch.setattr(
        "app.core.security.wall_clock_now", lambda: issued_at + timedelta(minutes=6)
    )

    with pytest.raises(InvalidAccessTokenError):
        verify_access_token(token, secret=JWT_TEST_SECRET)


def test_token_rejects_invalid_signature() -> None:
    token = create_access_token(
        user_id=uuid4(),
        role=UserRole.COORDINATOR,
        secret=SecretStr("correct-test-secret-with-32-byte-minimum"),
        expires_minutes=5,
    )

    with pytest.raises(InvalidAccessTokenError):
        verify_access_token(
            token,
            secret=SecretStr("wrong-test-secret-with-32-byte-minimum"),
        )
