"""Stable cursor slices, masked previews, and read receipts."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationError
from app.models.enums import MessageStatus
from app.repositories.donor import DonorRepository
from app.repositories.simulator_conversations import ConversationRecord, ConversationRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.services.simulator.query import SimulatorQueryService
from app.services.simulator.receipts import SimulatorReceiptService
from tests.integration.messaging_fixtures import FixedClock
from tests.services.simulator_fixtures import NOW, Publisher, donor, message


@pytest.mark.asyncio
async def test_message_page_is_chronological_and_uses_stable_tie_breaker() -> None:
    person = donor()
    donors, messages = AsyncMock(spec=DonorRepository), AsyncMock(spec=SimulatorMessageRepository)
    donors.get.return_value = person
    rows = [message(person) for _ in range(3)]
    for index, row in enumerate(rows):
        row.id = UUID(int=3 - index)
    messages.visible_page.return_value = tuple(rows)
    service = SimulatorQueryService(donors, AsyncMock(spec=ConversationRepository), messages)
    page = await service.messages(person.id, before=None, limit=2)
    assert [item.id for item in page.items] == [UUID(int=2), UUID(int=3)]
    assert page.next_before == UUID(int=2)
    messages.get.return_value = rows[1]
    messages.visible_page.return_value = (rows[2],)
    older = await service.messages(person.id, before=page.next_before, limit=2)
    messages.visible_page.assert_awaited_with(person.id, before=(NOW, UUID(int=2)), limit=3)
    assert older.next_before is None


@pytest.mark.asyncio
async def test_foreign_cursor_rejected() -> None:
    donors, messages = AsyncMock(spec=DonorRepository), AsyncMock(spec=SimulatorMessageRepository)
    donors.get.return_value = donor()
    messages.get.return_value = message(donor())
    service = SimulatorQueryService(donors, AsyncMock(spec=ConversationRepository), messages)
    with pytest.raises(ValidationError, match="Cursor"):
        await service.messages(donors.get.return_value.id, before=uuid4(), limit=20)


@pytest.mark.asyncio
async def test_conversation_preview_masks_phone_and_retains_unreachable_flag() -> None:
    person, conversations = donor(), AsyncMock(spec=ConversationRepository)
    person.sim_reachable = False
    conversations.list_threads.return_value = (
        (ConversationRecord(person, message(person), uuid4(), "Recall", 3),),
        1,
    )
    service = SimulatorQueryService(
        AsyncMock(spec=DonorRepository), conversations, AsyncMock(spec=SimulatorMessageRepository)
    )
    page = await service.conversations(campaign_id=None, search="Test", page=1, page_size=20)
    assert page.items[0].donor.phone == "+92300*****67"
    assert page.items[0].donor.sim_reachable is False
    assert page.items[0].unread_count == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("receipts", [True, False])
async def test_open_marks_only_delivered_messages_and_respects_receipt_flag(receipts: bool) -> None:
    session, person = AsyncMock(spec=AsyncSession), donor()
    person.sim_read_receipts = receipts
    donors, messages = AsyncMock(spec=DonorRepository), AsyncMock(spec=SimulatorMessageRepository)
    donors.get.return_value = person
    delivered = message(person)
    messages.delivered_outbound_for_update.return_value = (delivered,)
    publisher = Publisher(session)
    service = SimulatorReceiptService(session, donors, messages, publisher, FixedClock(NOW))
    result = await service.open(person.id)
    assert result.read_count == int(receipts)
    assert delivered.status == (MessageStatus.READ if receipts else MessageStatus.DELIVERED)
    assert len(publisher.events) == (2 if receipts else 0)
    if not receipts:
        messages.delivered_outbound_for_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_receipt_commit_failure_publishes_nothing() -> None:
    session, person = AsyncMock(spec=AsyncSession), donor()
    donors, messages = AsyncMock(spec=DonorRepository), AsyncMock(spec=SimulatorMessageRepository)
    donors.get.return_value = person
    messages.delivered_outbound_for_update.return_value = (message(person),)
    session.commit.side_effect = RuntimeError("commit failed")
    publisher = Publisher(session)
    service = SimulatorReceiptService(session, donors, messages, publisher, FixedClock(NOW))
    with pytest.raises(RuntimeError):
        await service.open(person.id)
    assert not publisher.events
