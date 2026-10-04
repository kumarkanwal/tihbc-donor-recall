"""Tests for the generic repository operations."""

from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import Segment
from app.repositories.base import BaseRepository


@pytest.mark.asyncio
async def test_get_returns_session_entity() -> None:
    entity = Segment(id=uuid4(), key="regular", label="Regular")
    session_mock = Mock(spec=AsyncSession)
    session_mock.get = AsyncMock(return_value=entity)
    repository = BaseRepository(cast(AsyncSession, session_mock), Segment)

    result = await repository.get(entity.id)

    assert result is entity
    session_mock.get.assert_awaited_once_with(Segment, entity.id)


@pytest.mark.asyncio
async def test_list_returns_typed_page() -> None:
    entities = (
        Segment(id=uuid4(), key="lapsed", label="Lapsed"),
        Segment(id=uuid4(), key="regular", label="Regular"),
    )
    scalar_result = Mock()
    scalar_result.all.return_value = list(entities)
    execute_result = Mock()
    execute_result.scalars.return_value = scalar_result
    session_mock = Mock(spec=AsyncSession)
    session_mock.execute = AsyncMock(return_value=execute_result)
    session_mock.scalar = AsyncMock(return_value=5)
    repository = BaseRepository(cast(AsyncSession, session_mock), Segment)

    result = await repository.list(page=2, page_size=2)

    assert result.items == entities
    assert result.total == 5
    assert result.page == 2
    assert result.page_size == 2


@pytest.mark.asyncio
async def test_add_flushes_without_committing() -> None:
    entity = Segment(id=uuid4(), key="first_time", label="First-time")
    session_mock = Mock(spec=AsyncSession)
    session_mock.flush = AsyncMock()
    repository = BaseRepository(cast(AsyncSession, session_mock), Segment)

    result = await repository.add(entity)

    assert result is entity
    session_mock.add.assert_called_once_with(entity)
    session_mock.flush.assert_awaited_once_with()
    session_mock.commit.assert_not_called()
