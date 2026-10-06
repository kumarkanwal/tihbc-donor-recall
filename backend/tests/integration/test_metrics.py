"""PostgreSQL acceptance tests for dashboard metrics and reports."""

from collections.abc import AsyncIterator
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user
from app.core.db import get_db
from app.main import app
from app.models.campaign import Campaign, Enrollment
from app.models.enums import (
    CampaignStatus,
    EnrollmentStatus,
    LanguageCode,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    ResponseIntent,
    ResponseSource,
    SeriesKind,
    UserRole,
)
from app.models.message import Message
from app.models.response import DonorResponse
from app.schemas.user import UserOut
from tests.integration.campaign_fixtures import add_campaign_fixture
from tests.services.simulator_fixtures import NOW

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_metrics_reports_and_exports_match_frontend_contract(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        campaign, user = await _add_metrics_fixture(session)
        await session.commit()

        async def override_db() -> AsyncIterator[AsyncSession]:
            yield session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                overview = await client.get(
                    "/api/v1/metrics/overview",
                    params={"campaign_id": str(campaign.id)},
                )
                assert overview.status_code == 200
                assert overview.json() == {
                    "donors": 2,
                    "sent": 1,
                    "delivered": 1,
                    "read": 1,
                    "responded": 1,
                    "delivery_rate": 100.0,
                    "read_rate": 100.0,
                    "response_rate": 50.0,
                    "confirmed": 1,
                    "rescheduled": 0,
                    "declined": 0,
                    "escalated": 0,
                    "invalid_numbers": 1,
                    "undeliverable": 1,
                }
                demo_day = NOW.astimezone(ZoneInfo("Asia/Karachi")).date().isoformat()
                dated = await client.get(
                    "/api/v1/metrics/overview",
                    params={
                        "campaign_id": str(campaign.id),
                        "from": demo_day,
                        "to": demo_day,
                    },
                )
                assert dated.json()["sent"] == 1

                timeseries = await client.get("/api/v1/metrics/timeseries")
                assert timeseries.status_code == 200
                assert timeseries.json()["items"][0]["sent"] == 1
                assert timeseries.json()["items"][0]["responded"] == 1

                breakdown = await client.get("/api/v1/metrics/response-breakdown")
                assert breakdown.json()["by_intent"] == {"confirm": 1}
                assert breakdown.json()["by_language"] == {"en": 1}

                reasons = await client.get("/api/v1/metrics/decline-reasons")
                assert reasons.json() == {"items": []}

                campaigns = await client.get("/api/v1/metrics/campaigns")
                campaign_row = next(
                    row
                    for row in campaigns.json()["items"]
                    if row["campaign_id"] == str(campaign.id)
                )
                assert campaign_row["response_rate"] == 50.0

                inactive = await client.get(
                    "/api/v1/reports/inactive-numbers",
                    params={"campaign_id": str(campaign.id)},
                )
                assert inactive.status_code == 200
                assert inactive.json()["summary"] == {
                    "invalid": 1,
                    "undeliverable": 1,
                    "total": 2,
                }
                assert {row["kind"] for row in inactive.json()["items"]} == {
                    "invalid",
                    "undeliverable",
                }

                for report in ("inactive-numbers", "response-breakdown", "campaigns"):
                    exported = await client.get(f"/api/v1/reports/{report}/export")
                    assert exported.status_code == 200
                    assert exported.headers["content-type"].startswith("text/csv")
        finally:
            app.dependency_overrides.clear()


async def _add_metrics_fixture(session: AsyncSession) -> tuple[Campaign, UserOut]:
    base = await add_campaign_fixture(session, donor_languages=(LanguageCode.EN, LanguageCode.UR))
    base.batch.invalid_rows = 1
    base.batch.validation_report = [
        {"row": 4, "field": "phone", "value": "0300bad", "reason": "Invalid number"}
    ]
    campaign = Campaign(
        name="Metrics Campaign",
        batch=base.batch,
        primary_series=base.primary,
        secondary_series=base.secondary,
        status=CampaignStatus.RUNNING,
        start_at=NOW,
        launched_at=NOW,
        created_by=base.user,
        created_at=NOW,
        updated_at=NOW,
    )
    confirmed = Enrollment(
        campaign=campaign,
        donor=base.donors[0],
        status=EnrollmentStatus.CONFIRMED,
        current_series_kind=SeriesKind.PRIMARY,
        responded_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    undeliverable = Enrollment(
        campaign=campaign,
        donor=base.donors[1],
        status=EnrollmentStatus.UNDELIVERABLE,
        current_series_kind=SeriesKind.PRIMARY,
        created_at=NOW,
        updated_at=NOW,
    )
    sent = _message(confirmed, MessageDirection.OUTBOUND, "Recall", MessageStatus.READ)
    sent.sent_at = sent.delivered_at = sent.read_at = NOW
    inbound = _message(confirmed, MessageDirection.INBOUND, "Yes", MessageStatus.DELIVERED)
    inbound.sent_at = inbound.delivered_at = NOW
    failed = _message(undeliverable, MessageDirection.OUTBOUND, "Recall", MessageStatus.FAILED)
    failed.failed_reason = "Number not on WhatsApp"
    response = DonorResponse(
        enrollment=confirmed,
        message=inbound,
        intent=ResponseIntent.CONFIRM,
        source=ResponseSource.AGENT,
        detected_language="en",
        confidence=Decimal("0.98"),
        created_at=NOW,
        updated_at=NOW,
    )
    session.add_all((campaign, confirmed, undeliverable, sent, inbound, failed, response))
    await session.flush()
    user = UserOut.model_validate(base.user)
    user.role = UserRole.COORDINATOR
    return campaign, user


def _message(
    enrollment: Enrollment,
    direction: MessageDirection,
    body: str,
    status: MessageStatus,
) -> Message:
    return Message(
        donor=enrollment.donor,
        enrollment=enrollment,
        direction=direction,
        kind=MessageKind.TEXT,
        body=body,
        media_type=MediaType.NONE,
        status=status,
        scheduled_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
