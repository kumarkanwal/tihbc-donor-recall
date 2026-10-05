"""Authentication business logic."""

import structlog
from pydantic import SecretStr

from app.core.errors import UnauthorizedError
from app.core.logging import mask_email_address
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    InvalidAccessTokenError,
    create_access_token,
    verify_access_token,
    verify_password,
)
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut

logger = structlog.get_logger(__name__)
INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
INVALID_TOKEN_MESSAGE = "Invalid or expired access token"


class AuthService:
    """Authenticate credentials and resolve access tokens to active users."""

    def __init__(
        self,
        user_repository: UserRepository,
        *,
        jwt_secret: SecretStr,
        jwt_expires_minutes: int,
    ) -> None:
        self._users = user_repository
        self._jwt_secret = jwt_secret
        self._jwt_expires_minutes = jwt_expires_minutes

    async def authenticate(self, request: LoginRequest) -> TokenResponse:
        """Authenticate credentials and return a bearer token."""
        normalized_email = request.email.strip().lower()
        user = await self._users.get_by_email(normalized_email)
        password = request.password.get_secret_value()
        password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
        password_valid = verify_password(password, password_hash)
        if user is None or not password_valid or not user.is_active:
            logger.warning("login_failed", email=mask_email_address(normalized_email))
            raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE)

        token = create_access_token(
            user_id=user.id,
            role=user.role,
            secret=self._jwt_secret,
            expires_minutes=self._jwt_expires_minutes,
        )
        logger.info("login_succeeded", user_id=str(user.id), role=user.role.value)
        return TokenResponse(access_token=token, user=UserOut.model_validate(user))

    async def get_current_user(self, token: str) -> UserOut:
        """Resolve a valid token to its current active database user."""
        try:
            claims = verify_access_token(
                token,
                secret=self._jwt_secret,
            )
        except InvalidAccessTokenError:
            raise UnauthorizedError(INVALID_TOKEN_MESSAGE) from None

        user = await self._users.get(claims.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(INVALID_TOKEN_MESSAGE)
        return UserOut.model_validate(user)
