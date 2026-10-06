"""Seed realistic simulator conversations, responses, and follow-ups."""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Enrollment
from app.models.enums import (
    DeclineReason,
    EnrollmentStatus,
    MediaType,
    MessageDirection,
    MessageKind,
    MessageStatus,
    ResponseIntent,
    ResponseSource,
)
from app.models.follow_up import FollowUpItem
from app.models.message import Message
from app.models.response import DonorResponse
from app.models.series import SeriesStep
from app.models.user import User
from app.schemas.content_series import QuickReplyButtonInput
from app.seed.campaigns import SeedCampaigns
from app.seed.followups import FOLLOW_UP_TYPES, build_follow_up
from app.services.appointments.centers import center_for_city
from app.services.replies.templates import render_reply
from app.services.templates.renderer import (
    ButtonTemplate,
    TemplateValues,
    localize_buttons,
    render_body,
)

TERMINAL_INTENTS = {
    EnrollmentStatus.CONFIRMED: ResponseIntent.CONFIRM,
    EnrollmentStatus.RESCHEDULED: ResponseIntent.RESCHEDULE,
    EnrollmentStatus.DECLINED: ResponseIntent.DECLINE,
}
BOT_REPLY_KEYS = {
    EnrollmentStatus.CONFIRMED: "confirm_thanks",
    EnrollmentStatus.RESCHEDULED: "reschedule_confirmed",
    EnrollmentStatus.DECLINED: "decline_closing",
}
DECLINE_REASONS = (
    DeclineReason.TRAVELLING,
    DeclineReason.HEALTH,
    DeclineReason.OTHER,
)


async def seed_conversations(
    session: AsyncSession,
    campaigns: SeedCampaigns,
    coordinator: User,
    now: datetime,
    timezone_display: str,
) -> tuple[int, int, int]:
    """Populate visible message history and coordinator work across live campaigns."""
    messages: list[Message] = []
    responses: list[DonorResponse] = []
    follow_ups: list[FollowUpItem] = []
    enrollments = (*campaigns.regular_enrollments, *campaigns.lapsed_enrollments)
    for index, enrollment in enumerate(enrollments):
        outbound = _outbound_message(enrollment, index, now, timezone_display)
        messages.append(outbound)
        if enrollment.status in TERMINAL_INTENTS:
            inbound, response = _response(enrollment, outbound, index, now)
            acknowledgement = _acknowledgement(
                enrollment,
                inbound,
                index,
                timezone_display,
            )
            messages.extend((inbound, acknowledgement))
            responses.append(response)
        if enrollment.status in FOLLOW_UP_TYPES:
            follow_ups.append(build_follow_up(enrollment, coordinator, index, now))
    session.add_all((*messages, *responses, *follow_ups))
    await session.flush()
    return len(messages), len(responses), len(follow_ups)


def _outbound_message(
    enrollment: Enrollment,
    index: int,
    now: datetime,
    timezone_display: str,
) -> Message:
    step = _visible_step(enrollment)
    sent_at = now - timedelta(days=1 + index % 7, hours=index % 9)
    body, buttons = _render_step(enrollment, step, timezone_display)
    status = _outbound_status(enrollment, index)
    message = Message(
        donor=enrollment.donor,
        enrollment=enrollment,
        step=step,
        direction=MessageDirection.OUTBOUND,
        kind=MessageKind.INTERACTIVE,
        body=body,
        media_type=step.media_type,
        media_url=step.media_url,
        buttons=buttons,
        status=status,
        scheduled_at=sent_at,
        failed_reason=("Simulated unreachable number" if status == MessageStatus.FAILED else None),
        provider_message_id=(
            f"seed-{enrollment.id.hex}" if status != MessageStatus.FAILED else None
        ),
        created_at=sent_at,
        updated_at=sent_at,
    )
    if status != MessageStatus.FAILED:
        message.sent_at = sent_at
    if status in {MessageStatus.DELIVERED, MessageStatus.READ}:
        message.delivered_at = sent_at + timedelta(seconds=8)
    if status == MessageStatus.READ:
        message.read_at = sent_at + timedelta(seconds=45)
    return message


def _response(
    enrollment: Enrollment,
    outbound: Message,
    index: int,
    now: datetime,
) -> tuple[Message, DonorResponse]:
    intent = TERMINAL_INTENTS[enrollment.status]
    response_at = now - timedelta(days=index % 6, hours=2)
    body, button_id = _response_text(enrollment, intent, index)
    inbound = Message(
        donor=enrollment.donor,
        enrollment=enrollment,
        direction=MessageDirection.INBOUND,
        kind=MessageKind.BUTTON_REPLY,
        body=body,
        media_type=MediaType.NONE,
        status=MessageStatus.DELIVERED,
        scheduled_at=response_at,
        sent_at=response_at,
        delivered_at=response_at,
        reply_to_message=outbound,
        button_id=button_id,
        created_at=response_at,
        updated_at=response_at,
    )
    decline_reason = (
        DECLINE_REASONS[index % len(DECLINE_REASONS)] if intent == ResponseIntent.DECLINE else None
    )
    enrollment.responded_at = response_at
    enrollment.decline_reason = decline_reason
    response = DonorResponse(
        enrollment=enrollment,
        message=inbound,
        intent=intent,
        source=ResponseSource.BUTTON,
        detected_language=enrollment.donor.language.value,
        decline_reason=decline_reason,
        confidence=Decimal("1.00"),
        created_at=response_at,
        updated_at=response_at,
    )
    return inbound, response


def _acknowledgement(
    enrollment: Enrollment,
    inbound: Message,
    index: int,
    timezone_display: str,
) -> Message:
    sent_at = inbound.sent_at + timedelta(seconds=2) if inbound.sent_at else inbound.created_at
    body = render_reply(
        BOT_REPLY_KEYS[enrollment.status],
        enrollment,
        enrollment.appointment_slot,
        timezone_display,
    )
    return Message(
        donor=enrollment.donor,
        enrollment=enrollment,
        direction=MessageDirection.OUTBOUND,
        kind=MessageKind.TEXT,
        body=body,
        media_type=MediaType.NONE,
        status=MessageStatus.READ if index % 4 else MessageStatus.DELIVERED,
        scheduled_at=sent_at,
        sent_at=sent_at,
        delivered_at=sent_at + timedelta(seconds=8),
        read_at=sent_at + timedelta(seconds=40) if index % 4 else None,
        provider_message_id=f"seed-reply-{enrollment.id.hex}",
        created_at=sent_at,
        updated_at=sent_at,
    )


def _visible_step(enrollment: Enrollment) -> SeriesStep:
    if enrollment.status in {EnrollmentStatus.IN_SECONDARY, EnrollmentStatus.ESCALATED}:
        steps = enrollment.campaign.secondary_series.steps
        return steps[-1] if enrollment.status == EnrollmentStatus.ESCALATED else steps[0]
    steps = enrollment.campaign.primary_series.steps
    order = min(enrollment.current_step_order or 1, len(steps))
    return steps[order - 1]


def _render_step(
    enrollment: Enrollment,
    step: SeriesStep,
    timezone_display: str,
) -> tuple[str, list[dict[str, str]]]:
    language = enrollment.donor.language
    content = next(item for item in step.contents if item.language == language)
    appointment = enrollment.appointment_slot
    body = render_body(
        content.body,
        language,
        TemplateValues(
            donor_name=enrollment.donor.full_name,
            center_name=(
                appointment.center_name
                if appointment is not None
                else center_for_city(enrollment.donor.city)
            ),
            appointment_date=appointment.starts_at if appointment is not None else None,
        ),
        timezone_display,
    )
    button_inputs = [QuickReplyButtonInput.model_validate(button) for button in step.buttons]
    localized = localize_buttons(
        [
            ButtonTemplate(id=button.id, intent=button.intent, labels=button.labels)
            for button in button_inputs
        ],
        language,
    )
    buttons = [
        {"id": button.id, "intent": button.intent, "label": button.label} for button in localized
    ]
    return body, buttons


def _outbound_status(enrollment: Enrollment, index: int) -> MessageStatus:
    if enrollment.status == EnrollmentStatus.UNDELIVERABLE:
        return MessageStatus.FAILED
    if enrollment.status in TERMINAL_INTENTS:
        return MessageStatus.READ
    if index % 7 == 0:
        return MessageStatus.SENT
    return MessageStatus.READ if enrollment.donor.sim_read_receipts else MessageStatus.DELIVERED


def _response_text(
    enrollment: Enrollment,
    intent: ResponseIntent,
    index: int,
) -> tuple[str, str]:
    urdu = enrollment.donor.language.value == "ur"
    if intent == ResponseIntent.CONFIRM:
        return ("تصدیق کریں" if urdu else "Confirm", "btn_confirm")
    if intent == ResponseIntent.RESCHEDULE:
        return ("دوسرا وقت" if urdu else "Reschedule", "btn_reschedule")
    reason = DECLINE_REASONS[index % len(DECLINE_REASONS)]
    labels = {
        DeclineReason.TRAVELLING: ("سفر میں ہوں", "Travelling", "btn_reason_travelling"),
        DeclineReason.HEALTH: ("صحت کی وجہ", "Health reason", "btn_reason_health"),
        DeclineReason.OTHER: ("کوئی اور وجہ", "Other", "btn_reason_other"),
    }
    urdu_label, english_label, button_id = labels[reason]
    return (urdu_label if urdu else english_label, button_id)
