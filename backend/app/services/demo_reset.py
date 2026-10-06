"""Guarded transactional reset for the demo environment."""

from dataclasses import asdict

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import ForbiddenError
from app.repositories.demo_reset import DemoResetRepository
from app.seed.full import reset_and_seed_demo_data

logger = structlog.get_logger(__name__)


class DemoResetService:
    """Reset operational demo data and restore foundational seed records."""

    def __init__(
        self,
        session: AsyncSession,
        repository: DemoResetRepository,
        settings: Settings,
        current_clock: Clock,
    ) -> None:
        self._session = session
        self._repository = repository
        self._settings = settings
        self._clock = current_clock

    async def reset(self) -> None:
        """Clear demo aggregates and restore configured users and slots."""
        if not self._settings.demo_mode:
            raise ForbiddenError("Demo data reset is disabled")

        try:
            summary = await reset_and_seed_demo_data(
                self._session,
                self._settings,
                self._clock,
                self._repository,
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        logger.info(
            "demo_data_reset",
            **asdict(summary),
        )
