"""Campaign route authorization tests."""

from datetime import timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.deps import (
    get_campaign_query_service,
    get_campaign_service,
    get_current_user,
)
from app.core.clock import clock
from app.core.errors import NotFoundError
from app.main import app
from app.models.enums import UserRole
from app.schemas.campaign import CampaignPage, EnrollmentPage
from app.schemas.user import UserOut


class EmptyCampaignQueryService:
    """Return empty pages and deterministic missing-detail errors."""

    async def list_campaigns(self, **filters: object) -> CampaignPage:
        assert filters["page"] == 1
        return CampaignPage(items=[], total=0, page=1, page_size=20)

    async def get_campaign(self, campaign_id: UUID) -> None:
        del campaign_id
        raise NotFoundError("Campaign not found")

    async def list_enrollments(self, campaign_id: UUID, **filters: object) -> EnrollmentPage:
        del campaign_id
        assert filters["status"] is None
        return EnrollmentPage(items=[], total=0, page=1, page_size=20)

    async def get_enrollment(self, enrollment_id: UUID) -> None:
        del enrollment_id
        raise NotFoundError("Enrollment not found")


def test_coordinator_can_read_campaigns_and_enrollments() -> None:
    campaign_id = uuid4()
    enrollment_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.COORDINATOR)
    app.dependency_overrides[get_campaign_query_service] = EmptyCampaignQueryService
    try:
        client = TestClient(app)
        listed = client.get("/api/v1/campaigns")
        detail = client.get(f"/api/v1/campaigns/{campaign_id}")
        enrollments = client.get(f"/api/v1/campaigns/{campaign_id}/enrollments")
        enrollment = client.get(f"/api/v1/enrollments/{enrollment_id}")
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 200
    assert detail.status_code == 404
    assert enrollments.status_code == 200
    assert enrollment.status_code == 404


def test_coordinator_cannot_write_campaigns() -> None:
    campaign_id = uuid4()
    payload = {
        "name": "Blocked Campaign",
        "batch_id": str(uuid4()),
        "primary_series_id": str(uuid4()),
        "secondary_series_id": str(uuid4()),
        "start_at": (clock.now() + timedelta(days=1)).isoformat(),
    }
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.COORDINATOR)
    app.dependency_overrides[get_campaign_service] = object
    try:
        client = TestClient(app)
        responses = (
            client.post("/api/v1/campaigns", json=payload),
            client.patch(f"/api/v1/campaigns/{campaign_id}", json={"name": "Blocked"}),
            client.post(f"/api/v1/campaigns/{campaign_id}/actions/launch"),
            client.post(f"/api/v1/campaigns/{campaign_id}/actions/pause"),
            client.post(f"/api/v1/campaigns/{campaign_id}/actions/resume"),
        )
    finally:
        app.dependency_overrides.clear()

    assert {response.status_code for response in responses} == {403}
    assert {response.json()["error"]["code"] for response in responses} == {"FORBIDDEN"}


def test_campaign_routes_require_authentication() -> None:
    client = TestClient(app)

    assert client.get("/api/v1/campaigns").status_code == 401
    assert client.get(f"/api/v1/enrollments/{uuid4()}").status_code == 401


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(),
        email=f"{role.value}@example.test",
        full_name=role.value.title(),
        role=role,
        is_active=True,
    )
