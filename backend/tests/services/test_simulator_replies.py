"""Deterministic reply flows, persistence, and event ordering."""

from datetime import timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.agents.state import AgentResult
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.campaign import AppointmentSlot
from app.models.enums import (
    DeclineReason,
    EnrollmentStatus,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    ResponseIntent,
    ResponseSource,
)
from app.models.follow_up import FollowUpItem
from app.models.response import DonorResponse
from app.schemas.simulator import ButtonReply, TextReply
from tests.services.simulator_fixtures import NOW, ReplyFixture, reply_service


def _button(fixture: ReplyFixture, button_id: str, label: str, intent: str) -> ButtonReply:
    fixture.source.buttons = [{"id": button_id, "label": label, "intent": intent}]
    return ButtonReply(type="button", button_id=button_id, reply_to_message_id=fixture.source.id)


def _messages(fixture: ReplyFixture) -> list[object]:
    return [call.args[0] for call in fixture.messages.add.await_args_list]


def _response(fixture: ReplyFixture) -> DonorResponse:
    return next(
        call.args[0]
        for call in fixture.session.add.call_args_list
        if isinstance(call.args[0], DonorResponse)
    )


@pytest.mark.asyncio
async def test_confirm_updates_status_saves_response_and_uses_exact_reply() -> None:
    fixture = reply_service()
    request = _button(fixture, "btn_confirm", "Confirm", "confirm")

    result = await fixture.service.reply(fixture.person.id, request)

    inbound, outbound = _messages(fixture)
    assert result.direction == MessageDirection.INBOUND
    assert inbound.kind == MessageKind.BUTTON_REPLY
    assert fixture.enrollment.status == EnrollmentStatus.CONFIRMED
    assert fixture.enrollment.next_action_at is None
    assert fixture.enrollment.responded_at == NOW
    assert outbound.body.startswith(f"شکریہ {fixture.person.full_name}۔")
    response = _response(fixture)
    assert response.intent == ResponseIntent.CONFIRM
    assert response.source == ResponseSource.BUTTON
    assert response.confidence == 1
    assert fixture.follow_ups.add_with_activity.await_count == 1
    assert fixture.sleep.await_args.args == (1.5,)
    assert [event for event, _ in fixture.publisher.events] == [
        "simulator.typing",
        "message.created",
        "message.created",
        "simulator.typing",
        "enrollment.updated",
        "followup.created",
        "metrics.updated",
    ]
    assert fixture.publisher.events[0][1]["is_typing"] is True
    assert fixture.publisher.events[3][1]["is_typing"] is False


@pytest.mark.asyncio
async def test_reschedule_offers_three_localized_slots() -> None:
    fixture = reply_service()
    slots = tuple(
        AppointmentSlot(
            id=uuid4(),
            center_name="Korangi Campus Blood Center",
            starts_at=NOW + timedelta(days=index + 1),
            capacity=4,
            booked_count=0,
        )
        for index in range(3)
    )
    fixture.appointments.offer.return_value = slots
    request = _button(fixture, "btn_reschedule", "Reschedule", "reschedule")

    await fixture.service.reply(fixture.person.id, request)

    outbound = _messages(fixture)[1]
    assert fixture.enrollment.status == EnrollmentStatus.RESCHEDULE_REQUESTED
    assert len(outbound.buttons or []) == 3
    assert all(str(item["id"]).startswith("slot_") for item in outbound.buttons or [])
    assert outbound.body.startswith("کوئی مسئلہ نہیں۔")
    assert fixture.appointments.offer.await_args.args == (None,)


@pytest.mark.asyncio
async def test_slot_choice_books_under_service_and_confirms() -> None:
    fixture = reply_service()
    slot = AppointmentSlot(
        id=uuid4(),
        center_name="North Nazimabad Donor Center",
        starts_at=NOW + timedelta(days=2),
        capacity=4,
        booked_count=3,
    )
    fixture.enrollment.status = EnrollmentStatus.RESCHEDULE_REQUESTED
    fixture.appointments.book_selected.return_value = slot
    request = _button(fixture, f"slot_{slot.id.hex}", "Tue 7 Oct, 12:00 PM", "reschedule")

    await fixture.service.reply(fixture.person.id, request)

    assert fixture.enrollment.status == EnrollmentStatus.RESCHEDULED
    fixture.appointments.book_selected.assert_awaited_once_with(fixture.enrollment, slot.id)
    assert _messages(fixture)[1].body.startswith("ہو گیا۔")


@pytest.mark.asyncio
async def test_unclear_slot_choice_reoffers_once_then_escalates() -> None:
    first = reply_service()
    first.enrollment.status = EnrollmentStatus.RESCHEDULE_REQUESTED
    slot = AppointmentSlot(
        id=uuid4(),
        center_name="Korangi Campus Blood Center",
        starts_at=NOW + timedelta(days=1),
        capacity=4,
        booked_count=0,
    )
    first.source.buttons = [
        {"id": f"slot_{slot.id.hex}", "label": "Mon 6 Oct, 12:00 PM", "intent": "reschedule"}
    ]
    first.appointments.offer.return_value = (slot,)
    first.responses.unknown_count.return_value = 1

    await first.service.reply(first.person.id, TextReply(type="text", text="Maybe something else"))

    assert _messages(first)[1].buttons
    second = reply_service()
    second.enrollment.status = EnrollmentStatus.RESCHEDULE_REQUESTED
    second.source.buttons = first.source.buttons
    second.responses.unknown_count.return_value = 2
    await second.service.reply(second.person.id, TextReply(type="text", text="Still not sure"))
    item = second.follow_ups.add_with_activity.await_args.args[0]
    assert item.type == FollowUpType.NEEDS_CALL
    assert item.priority == FollowUpPriority.HIGH


@pytest.mark.asyncio
async def test_decline_asks_once_then_stores_reason_and_closes() -> None:
    first = reply_service()
    await first.service.reply(
        first.person.id,
        _button(first, "btn_decline", "Not now", "decline"),
    )
    question = _messages(first)[1]
    assert first.enrollment.status == EnrollmentStatus.DECLINED
    assert [item["id"] for item in question.buttons or []] == [
        "btn_reason_travelling",
        "btn_reason_health",
        "btn_reason_other",
    ]

    second = reply_service()
    second.enrollment.status = EnrollmentStatus.DECLINED
    await second.service.reply(
        second.person.id,
        _button(second, "btn_reason_health", "Health reason", "decline"),
    )
    assert second.enrollment.decline_reason == DeclineReason.HEALTH
    assert _response(second).decline_reason == DeclineReason.HEALTH
    assert _messages(second)[1].buttons is None
    assert _messages(second)[1].body.startswith("بتانے کا شکریہ۔")


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["Where is the center?", "asdfgh"])
async def test_question_and_unknown_create_high_priority_needs_call(text: str) -> None:
    fixture = reply_service()

    await fixture.service.reply(fixture.person.id, TextReply(type="text", text=text))

    item = fixture.follow_ups.add_with_activity.await_args.args[0]
    assert fixture.enrollment.status == EnrollmentStatus.IN_PRIMARY
    assert item.type == FollowUpType.NEEDS_CALL
    assert item.priority == FollowUpPriority.HIGH
    assert _messages(fixture)[1].body.startswith("شکریہ۔ ٹیم انڈس")


@pytest.mark.asyncio
async def test_llm_agent_classification_saves_trace_id_without_donor_pii() -> None:
    agent = AsyncMock()
    agent.run.return_value = AgentResult(
        intent=ResponseIntent.CONFIRM,
        confidence=0.96,
        detected_language="roman_ur",
        trace_id="trace-123",
    )
    fixture = reply_service(llm_enabled=True, agent=agent)

    await fixture.service.reply(
        fixture.person.id,
        TextReply(type="text", text="Ji main aaunga"),
    )

    response = _response(fixture)
    assert response.intent == ResponseIntent.CONFIRM
    assert response.trace_id == "trace-123"
    invocation = repr(agent.run.await_args.kwargs)
    assert fixture.person.full_name not in invocation
    assert fixture.person.phone_e164 not in invocation


@pytest.mark.asyncio
async def test_repeated_final_reply_adds_system_note_without_state_change() -> None:
    fixture = reply_service()
    fixture.enrollment.status = EnrollmentStatus.CONFIRMED
    existing = FollowUpItem(
        id=uuid4(),
        enrollment_id=fixture.enrollment.id,
        type=FollowUpType.CONFIRMED,
        status=FollowUpStatus.OPEN,
        priority=FollowUpPriority.NORMAL,
        created_at=NOW,
        updated_at=NOW,
    )
    fixture.follow_ups.open_for_enrollment.return_value = existing

    await fixture.service.reply(fixture.person.id, TextReply(type="text", text="Ji main aaunga"))

    assert fixture.enrollment.status == EnrollmentStatus.CONFIRMED
    activity = fixture.follow_ups.add_activity.await_args.args[0]
    assert activity.action == "note"
    assert activity.note == "Ji main aaunga"
    assert "followup.updated" in [event for event, _ in fixture.publisher.events]


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["foreign", "inbound", "failed", "unknown_button"])
async def test_button_reply_rejects_invalid_source_or_button(invalid: str) -> None:
    fixture = reply_service()
    if invalid == "foreign":
        fixture.source.donor_id = uuid4()
    if invalid == "inbound":
        fixture.source.direction = MessageDirection.INBOUND
    if invalid == "failed":
        fixture.source.status = MessageStatus.FAILED
    request = ButtonReply(
        type="button",
        button_id="bad" if invalid == "unknown_button" else "confirm",
        reply_to_message_id=fixture.source.id,
    )
    with pytest.raises(ValidationError):
        await fixture.service.reply(fixture.person.id, request)
    assert not fixture.messages.add.called and not fixture.publisher.events


@pytest.mark.asyncio
async def test_button_reply_cannot_be_submitted_twice() -> None:
    fixture = reply_service()
    fixture.messages.has_reply.return_value = True
    with pytest.raises(ConflictError, match="already"):
        await fixture.service.reply(
            fixture.person.id,
            ButtonReply(type="button", button_id="confirm", reply_to_message_id=fixture.source.id),
        )


@pytest.mark.asyncio
async def test_unreachable_and_missing_donors_rejected() -> None:
    fixture = reply_service()
    fixture.person.sim_reachable = False
    with pytest.raises(ConflictError, match="unreachable"):
        await fixture.service.reply(fixture.person.id, TextReply(type="text", text="Hello"))
    fixture.donors.get.return_value = None
    with pytest.raises(NotFoundError):
        await fixture.service.reply(fixture.person.id, TextReply(type="text", text="Hello"))


@pytest.mark.asyncio
async def test_commit_failure_rolls_back_and_does_not_publish() -> None:
    fixture = reply_service()
    fixture.session.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    with pytest.raises(RuntimeError, match="commit failed"):
        await fixture.service.reply(fixture.person.id, TextReply(type="text", text="Hello"))
    fixture.session.rollback.assert_awaited_once()
    assert fixture.publisher.events == []
