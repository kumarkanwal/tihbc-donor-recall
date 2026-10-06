"""PostgreSQL acceptance tests for settings and demo actions."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user
from app.core.clock import get_clock
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.main import app
from app.models.campaign import AppointmentSlot, Campaign
from app.models.demo_clock import DemoClock
from app.models.donor import Donor, DonorBatch
from app.models.enums import (
    CampaignStatus,
    DeclineReason,
    LanguageCode,
    MediaType,
    MessageCategory,
    SeriesKind,
    SeriesStatus,
    UserRole,
)
from app.models.follow_up import FollowUpItem
from app.models.message import Message
from app.models.response import DonorResponse
from app.models.series import ContentSeries, SeriesStep
from app.models.user import User
from app.schemas.user import UserOut
from tests.integration.campaign_fixtures import add_campaign_fixture
from tests.integration.messaging_fixtures import FixedClock
from tests.services.simulator_fixtures import NOW

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_settings_and_reset_match_frontend_contract(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_campaign_fixture(session)
        active_step = _step(fixture.primary, 1, MessageCategory.UTILITY)
        draft_series = _draft_series(fixture.user)
        draft_step = _step(draft_series, 1, MessageCategory.MARKETING)
        session.add_all((active_step, draft_series, draft_step))
        demo_clock = await session.get(DemoClock, 1)
        assert demo_clock is not None
        demo_clock.offset_seconds = 259_200
        await session.commit()

        current_user = UserOut.model_validate(fixture.user)
        settings = _seed_settings(fixture.user.email)

        async def override_db() -> AsyncIterator[AsyncSession]:
            yield session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: current_user
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_clock] = lambda: FixedClock(NOW)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                integration = await client.get("/api/v1/settings/integration")
                assert integration.status_code == 200
                assert integration.json() == {
                    "business_verified": True,
                    "phone_number": "+92 300 0000000",
                    "display_name": "TIHBC",
                    "quality_rating": "High",
                    "messaging_limit": 1000,
                    "templates": [
                        {
                            "name": f"{fixture.primary.name} - Step 1",
                            "status": "approved",
                            "category": "utility",
                        }
                    ],
                }

                current_user.role = UserRole.COORDINATOR
                denied = await client.post("/api/v1/demo/actions/reset-data")
                assert denied.status_code == 403

                current_user.role = UserRole.ADMIN
                reset = await client.post("/api/v1/demo/actions/reset-data")
                assert reset.status_code == 204
                assert reset.content == b""

                second_reset = await client.post("/api/v1/demo/actions/reset-data")
                assert second_reset.status_code == 204

            assert await session.scalar(select(func.count()).select_from(DonorBatch)) == 3
            assert await session.scalar(select(func.count()).select_from(Donor)) == 195
            assert await session.scalar(select(func.count()).select_from(ContentSeries)) == 4
            assert await session.scalar(select(func.count()).select_from(Campaign)) == 3
            assert await session.scalar(select(func.count()).select_from(AppointmentSlot)) == 336
            assert await session.scalar(select(func.count()).select_from(Message)) == 324
            assert await session.scalar(select(func.count()).select_from(DonorResponse)) == 82
            assert await session.scalar(select(func.count()).select_from(FollowUpItem)) == 100
            assert (
                await session.scalar(
                    select(func.count()).select_from(Donor).where(Donor.language == LanguageCode.UR)
                )
                == 117
            )
            assert (
                await session.scalar(
                    select(func.count()).select_from(Donor).where(Donor.sim_reachable.is_(False))
                )
                == 10
            )
            assert (
                await session.scalar(
                    select(func.count())
                    .select_from(Donor)
                    .where(Donor.sim_read_receipts.is_(False))
                )
                == 49
            )
            campaign_statuses = list(await session.scalars(select(Campaign.status)))
            assert campaign_statuses.count(CampaignStatus.RUNNING) == 2
            assert campaign_statuses.count(CampaignStatus.DRAFT) == 1
            decline_reasons = set(
                await session.scalars(
                    select(DonorResponse.decline_reason).where(
                        DonorResponse.decline_reason.is_not(None)
                    )
                )
            )
            assert decline_reasons == {
                DeclineReason.TRAVELLING,
                DeclineReason.HEALTH,
                DeclineReason.OTHER,
            }
            persisted_clock = await session.get(DemoClock, 1, populate_existing=True)
            assert persisted_clock is not None
            assert persisted_clock.offset_seconds == 259_200
            seeded_users = list(
                await session.scalars(
                    select(User).where(
                        User.email.in_((fixture.user.email, settings.seed_coordinator_email))
                    )
                )
            )
            assert {user.role for user in seeded_users} == {
                UserRole.ADMIN,
                UserRole.COORDINATOR,
            }
        finally:
            app.dependency_overrides.clear()


def _step(
    series: ContentSeries,
    step_order: int,
    category: MessageCategory,
) -> SeriesStep:
    return SeriesStep(
        series=series,
        step_order=step_order,
        delay_days=0,
        category=category,
        media_type=MediaType.NONE,
        buttons=[],
    )


def _draft_series(user: User) -> ContentSeries:
    token = uuid4().hex
    return ContentSeries(
        name=f"Draft {token}",
        kind=SeriesKind.PRIMARY,
        status=SeriesStatus.DRAFT,
        languages=[LanguageCode.EN],
        created_by=user,
    )


def _seed_settings(admin_email: str) -> Settings:
    return Settings().model_copy(
        update={
            "demo_mode": True,
            "seed_admin_email": admin_email,
            "seed_admin_password": SecretStr("AdminPassword123!"),
            "seed_coordinator_email": f"coordinator-{uuid4().hex}@example.test",
            "seed_coordinator_password": SecretStr("CoordinatorPassword123!"),
        }
    )
