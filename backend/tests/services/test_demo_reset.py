"""Tests for guarded demo reset orchestration."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import ForbiddenError
from app.repositories.demo_reset import DemoResetRepository
from app.services.demo_reset import DemoResetService


@pytest.mark.asyncio
async def test_demo_reset_is_disabled_outside_demo_mode() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=DemoResetRepository)
    settings = Settings().model_copy(update={"demo_mode": False})
    service = DemoResetService(session, repository, settings, Clock())

    with pytest.raises(ForbiddenError, match="disabled"):
        await service.reset()

    repository.truncate_demo_data.assert_not_awaited()
    session.commit.assert_not_awaited()
