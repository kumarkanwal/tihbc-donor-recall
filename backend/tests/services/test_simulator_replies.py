"""Reply storage, source validation, and scheduling suspension."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.enums import EnrollmentStatus, MessageDirection, MessageKind, MessageStatus
from app.schemas.simulator import ButtonReply, TextReply
from tests.services.simulator_fixtures import NOW, reply_service


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["text", "button"])
async def test_reply_stores_inbound_and_stops_steps_without_intent_handling(kind: str) -> None:
    service, session, _donors, messages, enrollments, publisher, person, source, enrollment = (
        reply_service()
    )
    request = (
        TextReply(type="text", text="Please call me")
        if kind == "text"
        else ButtonReply(type="button", button_id="confirm", reply_to_message_id=source.id)
    )
    result = await service.reply(person.id, request)
    assert result.direction == MessageDirection.INBOUND
    assert result.status == MessageStatus.DELIVERED
    assert result.read_at is None
    assert result.reply_to_message_id == source.id
    assert result.sent_at == result.delivered_at == NOW
    assert result.body == ("Please call me" if kind == "text" else "تصدیق کریں")
    assert result.kind == (MessageKind.TEXT if kind == "text" else MessageKind.BUTTON_REPLY)
    assert enrollment.status == EnrollmentStatus.IN_PRIMARY
    assert enrollment.next_action_at is None
    assert enrollment.responded_at == NOW
    assert messages.add.await_count == session.commit.await_count == 1
    enrollments.get_for_messaging_update.assert_awaited_once_with(enrollment.id)
    assert [kind for kind, _payload in publisher.events] == [
        "message.created",
        "enrollment.updated",
        "metrics.updated",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["foreign", "inbound", "failed", "unknown_button"])
async def test_button_reply_rejects_invalid_source_or_button(invalid: str) -> None:
    service, session, _donors, messages, _enrollments, publisher, person, source, _ = (
        reply_service()
    )
    if invalid == "foreign":
        source.donor_id = uuid4()
    if invalid == "inbound":
        source.direction = MessageDirection.INBOUND
    if invalid == "failed":
        source.status = MessageStatus.FAILED
    request = ButtonReply(
        type="button",
        button_id="bad" if invalid == "unknown_button" else "confirm",
        reply_to_message_id=source.id,
    )
    with pytest.raises(ValidationError):
        await service.reply(person.id, request)
    assert not messages.add.called and not session.commit.called and not publisher.events


@pytest.mark.asyncio
async def test_button_reply_cannot_be_submitted_twice() -> None:
    service, _, _, messages, _, _, person, source, _ = reply_service()
    messages.has_reply.return_value = True
    with pytest.raises(ConflictError, match="already"):
        await service.reply(
            person.id,
            ButtonReply(type="button", button_id="confirm", reply_to_message_id=source.id),
        )


@pytest.mark.asyncio
async def test_unreachable_and_missing_donors_rejected() -> None:
    service, _, donors, _, _, _, person, _, _ = reply_service()
    person.sim_reachable = False
    with pytest.raises(ConflictError, match="unreachable"):
        await service.reply(person.id, TextReply(type="text", text="Hello"))
    donors.get.return_value = None
    with pytest.raises(NotFoundError):
        await service.reply(person.id, TextReply(type="text", text="Hello"))


@pytest.mark.asyncio
async def test_commit_failure_does_not_publish_reply() -> None:
    service, session, _, _, _, publisher, person, _, _ = reply_service()
    session.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    with pytest.raises(RuntimeError, match="commit failed"):
        await service.reply(person.id, TextReply(type="text", text="Hello"))
    assert publisher.events == []
