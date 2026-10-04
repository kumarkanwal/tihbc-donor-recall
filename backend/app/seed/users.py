"""Create or update the configured demo staff users."""

import asyncio
from dataclasses import dataclass

import structlog
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.logging import configure_logging
from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SeedUser:
    """Configuration for one required demo user."""

    email: str
    full_name: str
    password: SecretStr
    role: UserRole


def configured_seed_users(settings: Settings) -> tuple[SeedUser, SeedUser]:
    """Build demo-user inputs or fail with missing variable names."""
    required = {
        "SEED_ADMIN_EMAIL": settings.seed_admin_email,
        "SEED_ADMIN_PASSWORD": settings.seed_admin_password,
        "SEED_COORDINATOR_EMAIL": settings.seed_coordinator_email,
        "SEED_COORDINATOR_PASSWORD": settings.seed_coordinator_password,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise RuntimeError(f"Missing seed settings: {', '.join(missing)}")
    assert settings.seed_admin_email is not None
    assert settings.seed_admin_password is not None
    assert settings.seed_coordinator_email is not None
    assert settings.seed_coordinator_password is not None
    return (
        SeedUser(
            email=settings.seed_admin_email,
            full_name="TIHBC Admin",
            password=settings.seed_admin_password,
            role=UserRole.ADMIN,
        ),
        SeedUser(
            email=settings.seed_coordinator_email,
            full_name="TIHBC Coordinator",
            password=settings.seed_coordinator_password,
            role=UserRole.COORDINATOR,
        ),
    )


async def upsert_demo_users(
    session: AsyncSession,
    seed_users: tuple[SeedUser, ...],
) -> tuple[User, ...]:
    """Create or update demo users without creating duplicates."""
    repository = UserRepository(session)
    users: list[User] = []
    for seed_user in seed_users:
        normalized_email = seed_user.email.strip().lower()
        user = await repository.get_by_email(normalized_email)
        if user is None:
            user = User(
                email=normalized_email,
                full_name=seed_user.full_name,
                password_hash=hash_password(seed_user.password.get_secret_value()),
                role=seed_user.role,
                is_active=True,
            )
            await repository.add(user)
        else:
            user.email = normalized_email
            user.full_name = seed_user.full_name
            user.role = seed_user.role
            user.is_active = True
            password = seed_user.password.get_secret_value()
            if not verify_password(password, user.password_hash):
                user.password_hash = hash_password(password)
        users.append(user)
    await session.flush()
    return tuple(users)


async def seed_users(settings: Settings | None = None) -> tuple[User, ...]:
    """Persist configured demo users in one transaction."""
    resolved_settings = settings or get_settings()
    resources = create_database_resources(resolved_settings.database_url)
    try:
        async with resources.session_factory.begin() as session:
            users = await upsert_demo_users(session, configured_seed_users(resolved_settings))
        logger.info("demo_users_seeded", user_ids=[str(user.id) for user in users])
        return users
    finally:
        await resources.engine.dispose()


async def main() -> None:
    """Run the demo-user seed command."""
    settings = get_settings()
    configure_logging(settings.log_level)
    await seed_users(settings)


if __name__ == "__main__":
    asyncio.run(main())
