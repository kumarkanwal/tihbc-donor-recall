"""Guarded transactional reset for the demo environment."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import ForbiddenError
from app.repositories.demo_reset import DemoResetRepository
from app.seed.slots import seed_appointment_slots
from app.seed.users import configured_seed_users, upsert_demo_users

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
            await self._repository.truncate_demo_data()
            users = await upsert_demo_users(
                self._session,
                configured_seed_users(self._settings),
            )
            slot_count = await seed_appointment_slots(
                self._session,
                self._clock,
                self._settings.timezone_display,
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        logger.info(
            "demo_data_reset",
            user_count=len(users),
            appointment_slot_count=slot_count,
        )
