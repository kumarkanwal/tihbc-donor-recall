"""Rollback-isolated fixtures for opt-in PostgreSQL tests."""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings


@pytest_asyncio.fixture
async def postgres_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Yield sessions on one outer transaction and roll back all test writes."""
    engine = create_async_engine(Settings().database_url, pool_pre_ping=True)
    try:
        connection = await engine.connect()
    except (OSError, SQLAlchemyError) as error:
        await engine.dispose()
        pytest.skip(f"PostgreSQL is not reachable: {type(error).__name__}")

    transaction = await connection.begin()
    session_factory = async_sessionmaker(
        connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session_factory
    finally:
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()
        await engine.dispose()
