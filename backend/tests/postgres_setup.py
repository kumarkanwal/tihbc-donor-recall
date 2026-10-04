"""Provision the isolated PostgreSQL database used by integration tests."""

import asyncio
from pathlib import Path

from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

DEFAULT_TEST_DATABASE_NAME = "tihbc_test"
MAINTENANCE_DATABASE_NAME = "postgres"


def resolve_test_database_url(
    development_database_url: str,
    configured_test_database_url: str | None,
) -> str:
    """Resolve a test URL and reject the configured development database."""
    development_url = make_url(development_database_url)
    test_url = _configured_or_default_url(development_url, configured_test_database_url)
    if _database_identity(test_url) == _database_identity(development_url):
        raise ValueError("TEST_DATABASE_URL must identify a different database than DATABASE_URL")
    return test_url.render_as_string(hide_password=False)


def prepare_test_database(test_database_url: str, *, alembic_config_path: Path) -> None:
    """Create the test database when needed and migrate it to Alembic head."""
    asyncio.run(_create_database_if_missing(make_url(test_database_url)))
    get_settings.cache_clear()
    alembic_upgrade(Config(str(alembic_config_path)), "head")


def _configured_or_default_url(
    development_url: URL,
    configured_test_database_url: str | None,
) -> URL:
    if configured_test_database_url and configured_test_database_url.strip():
        return make_url(configured_test_database_url)
    return development_url.set(database=DEFAULT_TEST_DATABASE_NAME)


def _database_identity(url: URL) -> tuple[str, str | None, int | None, str | None]:
    return (url.get_backend_name(), url.host, url.port, url.database)


async def _create_database_if_missing(test_url: URL) -> None:
    database_name = test_url.database
    if not database_name:
        raise ValueError("TEST_DATABASE_URL must include a database name")
    maintenance_url = test_url.set(database=MAINTENANCE_DATABASE_NAME)
    engine = create_async_engine(
        maintenance_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            )
            if exists is None:
                quoted_name = engine.dialect.identifier_preparer.quote(database_name)
                await connection.execute(text(f"CREATE DATABASE {quoted_name}"))
    finally:
        await engine.dispose()
