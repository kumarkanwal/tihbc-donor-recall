"""Authentication request and response schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, SecretStr

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    email: Annotated[str, Field(min_length=3, max_length=255)]
    password: Annotated[SecretStr, Field(min_length=1, max_length=256)]


class TokenResponse(BaseModel):
    """Access token and authenticated user returned after login."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut
