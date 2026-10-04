"""Wait for PostgreSQL before running container startup work."""

import asyncio
from collections.abc import Awaitable, Callable

import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)
MAX_WAIT_SECONDS = 60.0
RETRY_INTERVAL_SECONDS = 1.0
ReadinessProbe = Callable[[str], Awaitable[bool]]


async def postgres_is_ready(database_url: str) -> bool:
    """Return whether PostgreSQL accepts a simple query."""
    resources = create_database_resources(database_url)
    try:
        async with resources.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except (OSError, SQLAlchemyError):
        return False
    finally:
        await resources.engine.dispose()
    return True


async def wait_for_postgres(
    settings: Settings,
    *,
    max_wait_seconds: float = MAX_WAIT_SECONDS,
    retry_interval_seconds: float = RETRY_INTERVAL_SECONDS,
    readiness_probe: ReadinessProbe = postgres_is_ready,
) -> None:
    """Wait until PostgreSQL accepts a simple query or the deadline expires."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_wait_seconds
    while not await readiness_probe(settings.database_url):
        if loop.time() >= deadline:
            raise RuntimeError("PostgreSQL did not become ready before startup timeout")
        logger.info("waiting_for_postgres", retry_seconds=retry_interval_seconds)
        await asyncio.sleep(retry_interval_seconds)
    logger.info("postgres_ready")


async def main() -> None:
    """Configure logging and wait for the configured PostgreSQL server."""
    settings = get_settings()
    configure_logging(settings.log_level)
    await wait_for_postgres(settings)


if __name__ == "__main__":
    asyncio.run(main())
