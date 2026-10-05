"""Shared test environment configuration."""

import os
from pathlib import Path

import pytest

from app.core.config import Settings, get_settings
from tests.postgres_setup import prepare_test_database, resolve_test_database_url

TEST_ENVIRONMENT = {
    "APP_ENV": "development",
    "DEMO_MODE": "true",
    "CORS_ORIGINS": "http://localhost:3000",
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
    "REDIS_URL": "redis://localhost:6379/15",
    "JWT_SECRET": "test-secret",
    "MEDIA_STORAGE_DIR": "./test-media",
    "MEDIA_PUBLIC_URL": "http://localhost:8000/media",
    "MESSAGING_PROVIDER": "simulator",
    "LLM_ENABLED": "false",
    "LANGSMITH_TRACING": "false",
}
TEST_DATABASE_URL_KEY = pytest.StashKey[str]()
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the explicit live-PostgreSQL test switch."""
    parser.addoption(
        "--run-postgres",
        action="store_true",
        default=False,
        help="run tests marked postgres against the isolated TEST_DATABASE_URL",
    )
    parser.addoption(
        "--run-redis",
        action="store_true",
        default=False,
        help="run real Redis pub/sub tests on unique temporary channels",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Set isolated defaults and route database tests away from development data."""
    run_postgres = bool(config.getoption("--run-postgres"))
    database_url = TEST_ENVIRONMENT["DATABASE_URL"]
    redis_url = TEST_ENVIRONMENT["REDIS_URL"]
    if config.getoption("--run-redis"):
        redis_settings = Settings()
        redis_url = redis_settings.test_redis_url or redis_settings.redis_url
    if run_postgres:
        settings = Settings()
        database_url = resolve_test_database_url(
            settings.database_url,
            settings.test_database_url,
        )
        config.stash[TEST_DATABASE_URL_KEY] = database_url
    for variable_name, value in TEST_ENVIRONMENT.items():
        os.environ[variable_name] = value
    os.environ["DATABASE_URL"] = database_url
    os.environ["REDIS_URL"] = redis_url
    get_settings.cache_clear()


def pytest_sessionstart(session: pytest.Session) -> None:
    """Create and migrate the isolated PostgreSQL database before collection."""
    if not session.config.getoption("--run-postgres"):
        return
    prepare_test_database(
        session.config.stash[TEST_DATABASE_URL_KEY],
        alembic_config_path=BACKEND_ROOT / "alembic.ini",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip live PostgreSQL tests unless explicitly requested."""
    skip_postgres = pytest.mark.skip(reason="use --run-postgres to enable live database tests")
    for item in items:
        if "postgres" in item.keywords and not config.getoption("--run-postgres"):
            item.add_marker(skip_postgres)
        if "redis" in item.keywords and not config.getoption("--run-redis"):
            item.add_marker(pytest.mark.skip(reason="use --run-redis for real pub/sub tests"))
