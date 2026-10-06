"""PostgreSQL acceptance tests for the coordinator follow-up inbox."""

from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user, get_event_publisher
from app.core.db import get_db
from app.main import app
from app.models.campaign import Campaign, Enrollment
from app.models.enums import (
    CampaignStatus,
    EnrollmentStatus,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
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
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.models.message import Message
from app.models.response import DonorResponse
from app.schemas.user import UserOut
from tests.integration.campaign_fixtures import add_campaign_fixture
from tests.integration.messaging_fixtures import RecordingPublisher
from tests.services.simulator_fixtures import NOW

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_follow_up_inbox_filters_mutates_audits_and_exports(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        item, user = await _add_follow_up(session)
        await session.commit()
        item_id = item.id
        publisher = RecordingPublisher(session)

        async def override_db() -> AsyncIterator[AsyncSession]:
            yield session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_event_publisher] = lambda: publisher
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                listed = await client.get(
                    "/api/v1/follow-ups",
                    params={"type": "confirmed", "status": "open", "search": "I will come"},
                )
                assert listed.status_code == 200
                assert listed.json()["items"][0]["latest_reply"]["body"] == "I will come"

                summary = await client.get("/api/v1/follow-ups/summary")
                assert summary.json()["by_type"]["confirmed"] == 1
                assert summary.json()["by_status"]["open"] == 1

                detail = await client.get(f"/api/v1/follow-ups/{item_id}")
                assert detail.json()["latest_response"]["raw_text"] == "I will come"

                updated = await client.patch(
                    f"/api/v1/follow-ups/{item_id}",
                    json={"status": "in_progress", "assigned_to_id": str(user.id)},
                )
                assert updated.status_code == 200
                assert updated.json()["assigned_to"]["id"] == str(user.id)

                noted = await client.post(
                    f"/api/v1/follow-ups/{item_id}/notes",
                    json={"note": "Called donor"},
                )
                assert noted.status_code == 200
                assert noted.json()["activities"][0]["note"] == "Called donor"

                resolved = await client.post(
                    f"/api/v1/follow-ups/{item_id}/actions/resolve",
                    json={"outcome": "attended", "note": "Donation completed"},
                )
                assert resolved.status_code == 200
                assert resolved.json()["status"] == "done"

                exported = await client.get("/api/v1/follow-ups/export")
                assert exported.status_code == 200
                assert "donor_name,phone,campaign" in exported.text
                assert "Follow-up Donor" in exported.text
        finally:
            app.dependency_overrides.clear()

        actions = list(
            await session.scalars(
                select(FollowUpActivity.action).where(FollowUpActivity.follow_up_id == item_id)
            )
        )
        assert {"created", "status_changed", "assigned", "note", "resolved"} <= set(actions)
        assert [event for event, _ in publisher.events] == ["followup.updated"] * 3


async def _add_follow_up(session: AsyncSession) -> tuple[FollowUpItem, UserOut]:
    base = await add_campaign_fixture(session, donor_languages=(LanguageCode.EN,))
    donor = base.donors[0]
    donor.full_name = "Follow-up Donor"
    campaign = Campaign(
        name="Follow-up Campaign",
        batch=base.batch,
        primary_series=base.primary,
        secondary_series=base.secondary,
        status=CampaignStatus.RUNNING,
        start_at=NOW,
        launched_at=NOW,
        created_by=base.user,
    )
    enrollment = Enrollment(
        campaign=campaign,
        donor=donor,
        status=EnrollmentStatus.CONFIRMED,
        current_series_kind=SeriesKind.PRIMARY,
        responded_at=NOW,
    )
    message = Message(
        donor=donor,
        enrollment=enrollment,
        direction=MessageDirection.INBOUND,
        kind=MessageKind.TEXT,
        body="I will come",
        media_type=MediaType.NONE,
        status=MessageStatus.DELIVERED,
        scheduled_at=NOW,
        sent_at=NOW,
        delivered_at=NOW,
    )
    response = DonorResponse(
        enrollment=enrollment,
        message=message,
        intent=ResponseIntent.CONFIRM,
        source=ResponseSource.AGENT,
        detected_language="en",
        confidence=Decimal("0.95"),
    )
    item = FollowUpItem(
        enrollment=enrollment,
        type=FollowUpType.CONFIRMED,
        status=FollowUpStatus.OPEN,
        priority=FollowUpPriority.NORMAL,
    )
    session.add_all(
        (
            campaign,
            enrollment,
            message,
            response,
            item,
            FollowUpActivity(follow_up=item, action="created"),
        )
    )
    await session.flush()
    user = UserOut.model_validate(base.user)
    user.role = UserRole.COORDINATOR
    return item, user
