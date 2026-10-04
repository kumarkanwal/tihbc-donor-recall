"""Tests for reusable role dependencies."""

from uuid import uuid4

import pytest

from app.api.deps import require_role
from app.core.errors import ForbiddenError
from app.models.enums import UserRole
from app.schemas.user import UserOut


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(),
        email="staff@tihbc.demo",
        full_name="Staff User",
        role=role,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_require_role_allows_listed_role() -> None:
    dependency = require_role(UserRole.ADMIN)
    admin = _user(UserRole.ADMIN)

    assert await dependency(admin) is admin


@pytest.mark.asyncio
async def test_require_role_blocks_unlisted_role() -> None:
    dependency = require_role(UserRole.ADMIN)

    with pytest.raises(ForbiddenError):
        await dependency(_user(UserRole.COORDINATOR))
