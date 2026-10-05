"""PostgreSQL HTTP simulator flow and stable message cursors."""

from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user, get_event_publisher
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.main import app
from app.models.campaign import Enrollment
from app.models.enums import (
    EnrollmentStatus,
    FollowUpType,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    UserRole,
)
from app.models.follow_up import FollowUpItem
from app.models.message import Message
from app.models.response import DonorResponse
from app.schemas.user import UserOut
from app.services.messaging.dependencies import build_delivery_service, build_messaging_service
from tests.integration.messaging_fixtures import (
    FixedClock,
    RecordingPublisher,
    add_messaging_fixture,
)
from tests.services.simulator_fixtures import NOW

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_simulator_http_reply_applies_deterministic_flow(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW)
        await session.commit()
        publisher = RecordingPublisher(session)
        service = build_messaging_service(session, Settings(), FixedClock(NOW), publisher)
        sent = await service.send_next_step(fixture.enrollment.id)
        assert sent is not None
        message = await session.get(Message, sent.message_id)
        assert message is not None
        message.status = MessageStatus.DELIVERED
        message.delivered_at = NOW
        await session.commit()

        async def override_db() -> AsyncIterator[AsyncSession]:
            yield session

        user = UserOut.model_validate(fixture.campaign_fixture.user)
        user.role = UserRole.COORDINATOR
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_event_publisher] = lambda: publisher
        app.dependency_overrides[get_settings] = lambda: Settings().model_copy(
            update={"sim_typing_seconds": 0}
        )
        path = f"/api/v1/simulator/conversations/{fixture.enrollment.donor_id}"
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                conversations = await client.get(
                    "/api/v1/simulator/conversations",
                    params={"campaign_id": str(fixture.campaign.id)},
                )
                assert conversations.status_code == 200
                row = conversations.json()["items"][0]
                assert row["donor"]["id"] == str(fixture.enrollment.donor_id)
                assert "*****" in row["donor"]["phone"]
                assert row["unread_count"] == 1
                opened = await client.post(f"{path}/actions/open")
                assert opened.json()["read_count"] == 1
                repeated = await client.post(f"{path}/actions/open")
                assert repeated.json()["read_count"] == 0
                publisher.events.clear()
                button = {
                    "type": "button",
                    "button_id": "btn_confirm",
                    "reply_to_message_id": str(sent.message_id),
                }
                reply = await client.post(f"{path}/replies", json=button)
                assert reply.status_code == 201
                assert reply.json()["body"] == "Confirm"
                assert reply.json()["status"] == "delivered"
                assert [event for event, _ in publisher.events] == [
                    "simulator.typing",
                    "message.created",
                    "message.created",
                    "simulator.typing",
                    "enrollment.updated",
                    "followup.created",
                    "metrics.updated",
                ]
                assert (await client.post(f"{path}/replies", json=button)).status_code == 409
                text = await client.post(
                    f"{path}/replies", json={"type": "text", "text": "Please call me"}
                )
                assert text.status_code == 201
                updated_events = [
                    payload
                    for event_type, payload in publisher.events
                    if event_type == "followup.updated"
                ]
                assert len(updated_events) == 1
                assert updated_events[0]["updated_at"]
                history = await client.get(f"{path}/messages")
                assert len(history.json()["items"]) == 5
        finally:
            app.dependency_overrides.clear()
        enrollment = await session.get(Enrollment, fixture.enrollment.id)
        assert enrollment is not None and enrollment.next_action_at is None
        assert enrollment.status == EnrollmentStatus.CONFIRMED
        assert enrollment.responded_at is not None
        assert await service.send_next_step(enrollment.id) is None
        response_count = await session.scalar(
            select(func.count())
            .select_from(DonorResponse)
            .where(DonorResponse.enrollment_id == enrollment.id)
        )
        assert response_count == 2
        follow_up = await session.scalar(
            select(FollowUpItem).where(FollowUpItem.enrollment_id == enrollment.id)
        )
        assert follow_up is not None and follow_up.type == FollowUpType.NEEDS_CALL
        await build_delivery_service(
            session, Settings(), FixedClock(NOW + timedelta(days=1)), publisher
        ).advance()
        inbound = await session.get(Message, UUID(reply.json()["id"]))
        assert inbound is not None and inbound.status == MessageStatus.DELIVERED


@pytest.mark.asyncio
async def test_cursor_pages_preserve_timestamp_ties_and_hide_failed_messages(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    from app.repositories.donor import DonorRepository
    from app.repositories.simulator_conversations import ConversationRepository
    from app.repositories.simulator_messages import SimulatorMessageRepository
    from app.services.simulator.query import SimulatorQueryService

    async with postgres_session_factory() as session:
        fixture = await add_messaging_fixture(session, NOW, reachable=False)
        messages = [
            Message(
                id=uuid4(),
                donor_id=fixture.enrollment.donor_id,
                enrollment_id=fixture.enrollment.id,
                direction=MessageDirection.OUTBOUND,
                kind=MessageKind.TEXT,
                body=f"Reminder {index}",
                media_type=MediaType.NONE,
                status=MessageStatus.SENT,
                scheduled_at=NOW,
                created_at=NOW,
            )
            for index in range(5)
        ]
        failed = Message(
            donor_id=fixture.enrollment.donor_id,
            enrollment_id=fixture.enrollment.id,
            direction=MessageDirection.OUTBOUND,
            kind=MessageKind.TEXT,
            body="Failed",
            media_type=MediaType.NONE,
            status=MessageStatus.FAILED,
            scheduled_at=NOW,
            created_at=NOW,
        )
        session.add_all([*messages, failed])
        await session.commit()
        service = SimulatorQueryService(
            DonorRepository(session),
            ConversationRepository(session),
            SimulatorMessageRepository(session),
        )
        first = await service.messages(fixture.enrollment.donor_id, before=None, limit=2)
        second = await service.messages(
            fixture.enrollment.donor_id, before=first.next_before, limit=2
        )
        third = await service.messages(
            fixture.enrollment.donor_id, before=second.next_before, limit=2
        )
        returned_ids = [item.id for page in (third, second, first) for item in page.items]
        assert returned_ids == sorted(message.id for message in messages)
        assert third.next_before is None
        assert failed.id not in returned_ids
