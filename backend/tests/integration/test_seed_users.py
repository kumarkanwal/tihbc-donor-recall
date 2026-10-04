"""PostgreSQL coverage for idempotent demo-user seeding."""

from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.seed.users import SeedUser, upsert_demo_users

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_demo_user_seed_is_idempotent(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    unique_suffix = uuid4().hex
    admin_email = f"admin-{unique_suffix}@example.test"
    coordinator_email = f"coordinator-{unique_suffix}@example.test"
    seed_users = (
        SeedUser(
            email=admin_email.upper(),
            full_name="TIHBC Admin",
            password=SecretStr("AdminPassword123!"),
            role=UserRole.ADMIN,
        ),
        SeedUser(
            email=coordinator_email,
            full_name="TIHBC Coordinator",
            password=SecretStr("CoordinatorPassword123!"),
            role=UserRole.COORDINATOR,
        ),
    )

    async with postgres_session_factory.begin() as session:
        first_users = await upsert_demo_users(session, seed_users)
        first_ids = tuple(user.id for user in first_users)
        second_users = await upsert_demo_users(session, seed_users)
        persisted_users = list(
            await session.scalars(
                select(User).where(User.email.in_((admin_email, coordinator_email)))
            )
        )

    assert tuple(user.id for user in second_users) == first_ids
    assert len(persisted_users) == 2
    users_by_role = {user.role: user for user in persisted_users}
    assert verify_password("AdminPassword123!", users_by_role[UserRole.ADMIN].password_hash)
    assert verify_password(
        "CoordinatorPassword123!",
        users_by_role[UserRole.COORDINATOR].password_hash,
    )
