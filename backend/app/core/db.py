"""Async SQLAlchemy engine, session factory, and request dependency."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import cast

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@dataclass(frozen=True)
class DatabaseResources:
    """Database resources owned by the application lifecycle."""

    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]


def create_database_resources(database_url: str) -> DatabaseResources:
    """Create the async engine and its session factory."""
    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return DatabaseResources(engine=engine, session_factory=session_factory)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield one database session for a request."""
    resources = cast(DatabaseResources, request.app.state.database)
    async with resources.session_factory() as session:
        yield session
