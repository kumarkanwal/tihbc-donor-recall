"""PostgreSQL HTTP coverage for campaign and enrollment workflows."""

from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user
from app.core.clock import Clock, clock
from app.core.db import get_db
from app.core.errors import InvalidStateTransitionError
from app.main import app
from app.models.enums import CampaignStatus, EnrollmentStatus
from app.repositories.campaign import CampaignRepository
from app.schemas.user import UserOut
from app.services.campaigns.service import CampaignService
from tests.integration.campaign_fixtures import CampaignFixture, add_campaign_fixture

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_http_create_launch_detail_and_enrollments_flow(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_campaign_fixture(session)
        await session.commit()
        _override_database(session, fixture)
        try:
            async with _client() as client:
                created = await client.post(
                    "/api/v1/campaigns",
                    json=_campaign_payload(fixture, clock.now() - timedelta(minutes=1)),
                )
                campaign_id = created.json()["id"]
                updated = await client.patch(
                    f"/api/v1/campaigns/{campaign_id}",
                    json={"name": "Updated Campaign Name"},
                )
                launched = await client.post(f"/api/v1/campaigns/{campaign_id}/actions/launch")
                detail = await client.get(f"/api/v1/campaigns/{campaign_id}")
                listed = await client.get("/api/v1/campaigns", params={"status": "running"})
                batch_detail = await client.get(f"/api/v1/donor-batches/{fixture.batch.id}")
                enrollments = await client.get(f"/api/v1/campaigns/{campaign_id}/enrollments")
                filtered_enrollments = await client.get(
                    f"/api/v1/campaigns/{campaign_id}/enrollments",
                    params={"status": "pending", "search": "Donor 1"},
                )
                first_enrollment_id = enrollments.json()["items"][0]["id"]
                enrollment = await client.get(f"/api/v1/enrollments/{first_enrollment_id}")
                series_edit = await client.patch(
                    f"/api/v1/content-series/{fixture.primary.id}",
                    json={"name": "Blocked by live campaign"},
                )
                paused = await client.post(f"/api/v1/campaigns/{campaign_id}/actions/pause")
                resumed = await client.post(f"/api/v1/campaigns/{campaign_id}/actions/resume")
                forbidden_update = await client.patch(
                    f"/api/v1/campaigns/{campaign_id}",
                    json={"name": "Too Late"},
                )
                second = await client.post(
                    "/api/v1/campaigns",
                    json=_campaign_payload(fixture, clock.now()),
                )
                double_launch = await client.post(
                    f"/api/v1/campaigns/{second.json()['id']}/actions/launch"
                )
        finally:
            app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["status"] == "draft"
    assert updated.json()["name"] == "Updated Campaign Name"
    assert launched.status_code == 200
    assert launched.json()["status"] == "running"
    assert launched.json()["enrollment_count"] == 3
    counts = detail.json()["enrollment_counts"]
    assert set(counts) == {status.value for status in EnrollmentStatus}
    assert counts["pending"] == 3
    assert sum(counts.values()) == 3
    assert campaign_id in {item["id"] for item in listed.json()["items"]}
    assert batch_detail.json()["campaign_count"] == 1
    assert enrollments.json()["total"] == 3
    assert all(item["status"] == "pending" for item in enrollments.json()["items"])
    assert all(
        item["current_series_kind"] == "primary"
        and item["current_step_order"] is None
        and item["next_action_at"] == created.json()["start_at"]
        for item in enrollments.json()["items"]
    )
    assert filtered_enrollments.json()["total"] == 1
    assert "*****" in enrollments.json()["items"][0]["donor"]["phone_e164"]
    assert enrollment.json()["donor"]["phone_e164"].startswith("+923")
    assert "*****" not in enrollment.json()["donor"]["phone_e164"]
    assert enrollment.json()["timeline"] == []
    assert enrollment.json()["follow_up"] is None
    assert series_edit.status_code == 409
    assert paused.json()["status"] == "paused"
    assert resumed.json()["status"] == "running"
    assert forbidden_update.status_code == 409
    assert forbidden_update.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert double_launch.status_code == 422
    assert any(
        problem["field"] == "batch_id" and "already used" in problem["reason"]
        for problem in double_launch.json()["error"]["details"]["problems"]
    )


@pytest.mark.asyncio
async def test_scheduled_campaign_starts_only_when_due(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_campaign_fixture(session)
        await session.commit()
        start_at = clock.now() + timedelta(days=1)
        _override_database(session, fixture)
        try:
            async with _client() as client:
                created = await client.post(
                    "/api/v1/campaigns",
                    json=_campaign_payload(fixture, start_at),
                )
                campaign_id = UUID(created.json()["id"])
                launched = await client.post(f"/api/v1/campaigns/{campaign_id}/actions/launch")
            early_service = CampaignService(
                session,
                CampaignRepository(session),
                FixedClock(start_at - timedelta(seconds=1)),
            )
            with pytest.raises(InvalidStateTransitionError, match="not been reached"):
                await early_service.start_scheduled(campaign_id)
            due_service = CampaignService(
                session,
                CampaignRepository(session),
                FixedClock(start_at),
            )
            started = await due_service.start_scheduled(campaign_id)
            completed = await due_service.complete(campaign_id)
        finally:
            app.dependency_overrides.clear()

    assert launched.json()["status"] == "scheduled"
    assert started.status == CampaignStatus.RUNNING
    assert completed.status == CampaignStatus.COMPLETED


class FixedClock(Clock):
    """Clock with a fixed UTC value for due-start coverage."""

    def __init__(self, value: datetime) -> None:
        super().__init__()
        self._value = value

    def now(self) -> datetime:
        return self._value


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


def _override_database(session: AsyncSession, fixture: CampaignFixture) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: UserOut.model_validate(fixture.user)


def _campaign_payload(fixture: CampaignFixture, start_at: datetime) -> dict[str, str]:
    return {
        "name": f"Campaign {uuid4().hex}",
        "batch_id": str(fixture.batch.id),
        "primary_series_id": str(fixture.primary.id),
        "secondary_series_id": str(fixture.secondary.id),
        "start_at": start_at.isoformat(),
    }
