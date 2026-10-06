"""Tests for guarded demo reset orchestration."""

from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import ForbiddenError
from app.repositories.demo_reset import DemoResetRepository
from app.services.demo_reset import DemoResetService


class RecordingResetRepository:
    """Record whether guarded reset work reaches persistence."""

    def __init__(self) -> None:
        self.called = False

    async def truncate_demo_data(self) -> None:
        self.called = True


@pytest.mark.asyncio
async def test_demo_reset_is_disabled_outside_demo_mode() -> None:
    session = cast(AsyncSession, object())
    repository = RecordingResetRepository()
    settings = cast(Settings, SimpleNamespace(demo_mode=False))
    service = DemoResetService(
        session,
        cast(DemoResetRepository, repository),
        settings,
        Clock(),
    )

    with pytest.raises(ForbiddenError, match="disabled"):
        await service.reset()

    assert repository.called is False
