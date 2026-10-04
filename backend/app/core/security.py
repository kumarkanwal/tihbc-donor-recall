"""Password hashing and JWT access-token primitives."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from pydantic import SecretStr

from app.core.clock import Clock
from app.models.enums import UserRole

JWT_ALGORITHM = "HS256"
PASSWORD_HASHER = PasswordHasher()


class InvalidAccessTokenError(Exception):
    """An access token failed signature or claim validation."""


@dataclass(frozen=True)
class AccessTokenClaims:
    """Validated claims carried by an access token."""

    user_id: UUID
    role: UserRole
    issued_at: datetime
    expires_at: datetime


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a password matches an Argon2 hash."""
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


DUMMY_PASSWORD_HASH = hash_password("tihbc-authentication-dummy-password")


def create_access_token(
    *,
    user_id: UUID,
    role: UserRole,
    secret: SecretStr,
    expires_minutes: int,
    current_clock: Clock,
) -> str:
    """Create an HS256 access token using application-clock timestamps."""
    issued_at = current_clock.now()
    expires_at = issued_at + timedelta(minutes=expires_minutes)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, secret.get_secret_value(), algorithm=JWT_ALGORITHM)


def verify_access_token(
    token: str,
    *,
    secret: SecretStr,
    current_clock: Clock,
) -> AccessTokenClaims:
    """Verify signature, required claims, role, subject, and clock-based expiry."""
    try:
        payload: dict[str, object] = jwt.decode(
            token,
            secret.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            options={
                "require": ["sub", "role", "iat", "exp"],
                "verify_exp": False,
                "verify_iat": False,
            },
        )
        user_id = UUID(_string_claim(payload, "sub"))
        role = UserRole(_string_claim(payload, "role"))
        issued_at = datetime.fromtimestamp(_integer_claim(payload, "iat"), tz=UTC)
        expires_at = datetime.fromtimestamp(_integer_claim(payload, "exp"), tz=UTC)
    except (
        jwt.InvalidTokenError,
        KeyError,
        OSError,
        OverflowError,
        TypeError,
        ValueError,
    ) as error:
        raise InvalidAccessTokenError from error

    current_time = current_clock.now()
    if issued_at > current_time or expires_at <= issued_at or expires_at <= current_time:
        raise InvalidAccessTokenError
    return AccessTokenClaims(
        user_id=user_id,
        role=role,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def _string_claim(payload: dict[str, object], name: str) -> str:
    value = payload[name]
    if not isinstance(value, str) or not value:
        raise ValueError(f"Invalid {name} claim")
    return value


def _integer_claim(payload: dict[str, object], name: str) -> int:
    value = payload[name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid {name} claim")
    return value
