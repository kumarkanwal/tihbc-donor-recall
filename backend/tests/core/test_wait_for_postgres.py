"""Tests for container PostgreSQL startup waiting."""

import pytest

from app.core.config import Settings
from app.core.wait_for_postgres import wait_for_postgres


@pytest.mark.asyncio
async def test_wait_for_postgres_retries_until_ready() -> None:
    attempts = 0

    async def readiness_probe(database_url: str) -> bool:
        nonlocal attempts
        assert database_url
        attempts += 1
        return attempts == 2

    await wait_for_postgres(
        Settings(),
        max_wait_seconds=1,
        retry_interval_seconds=0,
        readiness_probe=readiness_probe,
    )

    assert attempts == 2


@pytest.mark.asyncio
async def test_wait_for_postgres_fails_after_deadline() -> None:
    async def readiness_probe(database_url: str) -> bool:
        assert database_url
        return False

    with pytest.raises(RuntimeError, match="startup timeout"):
        await wait_for_postgres(
            Settings(),
            max_wait_seconds=0,
            retry_interval_seconds=0,
            readiness_probe=readiness_probe,
        )
