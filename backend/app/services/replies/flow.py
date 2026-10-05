"""Apply deterministic reply outcomes to enrollments and follow-ups."""

from dataclasses import dataclass

from app.models.campaign import AppointmentSlot, Enrollment
from app.models.enums import (
    EnrollmentStatus,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
    ResponseIntent,
)
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.repositories.follow_up import FollowUpRepository
from app.repositories.response import DonorResponseRepository
from app.services.appointments.service import AppointmentService
from app.services.replies.classification import Classification
from app.services.replies.templates import decline_buttons, slot_buttons
from app.services.replies.transitions import transition_enrollment

FINAL_INTENTS = {
    EnrollmentStatus.CONFIRMED: ResponseIntent.CONFIRM,
    EnrollmentStatus.RESCHEDULED: ResponseIntent.RESCHEDULE,
    EnrollmentStatus.DECLINED: ResponseIntent.DECLINE,
}


@dataclass(frozen=True)
class FlowOutcome:
    """Reply side effects needed to build the automatic message and events."""

    template_key: str
    buttons: list[dict[str, object]]
    appointment: AppointmentSlot | None
    follow_up: FollowUpItem
    follow_up_created: bool


class ReplyFlow:
    """Own deterministic enrollment, appointment, and follow-up changes."""

    def __init__(
        self,
        appointments: AppointmentService,
        follow_ups: FollowUpRepository,
        responses: DonorResponseRepository,
        timezone_display: str,
    ) -> None:
        self._appointments = appointments
        self._follow_ups = follow_ups
        self._responses = responses
        self._timezone_display = timezone_display

    async def apply(
        self, enrollment: Enrollment, classification: Classification, inbound_text: str
    ) -> FlowOutcome:
        """Apply one structured classification under the enrollment lock."""
        if self._is_repeated_final(enrollment, classification):
            return await self._repeated_final(enrollment, inbound_text)
        if classification.intent == ResponseIntent.CONFIRM:
            return await self._confirm(enrollment)
        if classification.intent == ResponseIntent.RESCHEDULE:
            return await self._reschedule(enrollment, classification)
        if classification.intent == ResponseIntent.DECLINE:
            return await self._decline(enrollment, classification)
        if classification.awaiting == "slot_choice":
            return await self._unclear_slot_choice(enrollment)
        return await self._needs_call(enrollment)

    @staticmethod
    def _is_repeated_final(enrollment: Enrollment, classification: Classification) -> bool:
        if classification.decline_reason is not None or classification.selected_slot_id is not None:
            return False
        return FINAL_INTENTS.get(enrollment.status) == classification.intent

    async def _confirm(self, enrollment: Enrollment) -> FlowOutcome:
        transition_enrollment(enrollment, EnrollmentStatus.CONFIRMED)
        follow_up, created = await self._ensure_follow_up(
            enrollment, FollowUpType.CONFIRMED, FollowUpPriority.NORMAL
        )
        return FlowOutcome("confirm_thanks", [], enrollment.appointment_slot, follow_up, created)

    async def _reschedule(
        self, enrollment: Enrollment, classification: Classification
    ) -> FlowOutcome:
        if classification.selected_slot_id is not None:
            selected = await self._appointments.book_selected(
                enrollment, classification.selected_slot_id
            )
            if selected is not None:
                transition_enrollment(enrollment, EnrollmentStatus.RESCHEDULED)
                follow_up, created = await self._ensure_follow_up(
                    enrollment, FollowUpType.RESCHEDULE, FollowUpPriority.NORMAL
                )
                return FlowOutcome("reschedule_confirmed", [], selected, follow_up, created)
        transition_enrollment(enrollment, EnrollmentStatus.RESCHEDULE_REQUESTED)
        slots = await self._appointments.offer(classification.requested_date)
        if not slots:
            return await self._needs_call(enrollment, template_key="no_slots")
        follow_up, created = await self._ensure_follow_up(
            enrollment, FollowUpType.RESCHEDULE, FollowUpPriority.NORMAL
        )
        buttons = slot_buttons(slots, enrollment.donor.language, self._timezone_display)
        return FlowOutcome("reschedule_offer", buttons, None, follow_up, created)

    async def _decline(self, enrollment: Enrollment, classification: Classification) -> FlowOutcome:
        transition_enrollment(enrollment, EnrollmentStatus.DECLINED)
        if classification.decline_reason is not None:
            enrollment.decline_reason = classification.decline_reason
        follow_up, created = await self._ensure_follow_up(
            enrollment, FollowUpType.DECLINED, FollowUpPriority.NORMAL
        )
        if enrollment.decline_reason is not None:
            return FlowOutcome("decline_closing", [], None, follow_up, created)
        return FlowOutcome(
            "decline_ask_reason",
            decline_buttons(enrollment.donor.language),
            None,
            follow_up,
            created,
        )

    async def _needs_call(
        self, enrollment: Enrollment, *, template_key: str = "needs_call"
    ) -> FlowOutcome:
        follow_up, created = await self._ensure_follow_up(
            enrollment, FollowUpType.NEEDS_CALL, FollowUpPriority.HIGH
        )
        return FlowOutcome(template_key, [], None, follow_up, created)

    async def _unclear_slot_choice(self, enrollment: Enrollment) -> FlowOutcome:
        if await self._responses.unknown_count(enrollment.id) >= 2:
            return await self._needs_call(enrollment)
        slots = await self._appointments.offer()
        if not slots:
            return await self._needs_call(enrollment, template_key="no_slots")
        follow_up, created = await self._ensure_follow_up(
            enrollment, FollowUpType.RESCHEDULE, FollowUpPriority.NORMAL
        )
        return FlowOutcome(
            "reschedule_offer",
            slot_buttons(slots, enrollment.donor.language, self._timezone_display),
            None,
            follow_up,
            created,
        )

    async def _repeated_final(self, enrollment: Enrollment, inbound_text: str) -> FlowOutcome:
        follow_up_type = {
            EnrollmentStatus.CONFIRMED: FollowUpType.CONFIRMED,
            EnrollmentStatus.RESCHEDULED: FollowUpType.RESCHEDULE,
            EnrollmentStatus.DECLINED: FollowUpType.DECLINED,
        }[enrollment.status]
        follow_up, created = await self._ensure_follow_up(
            enrollment, follow_up_type, FollowUpPriority.NORMAL
        )
        await self._follow_ups.add_activity(
            FollowUpActivity(follow_up=follow_up, action="note", note=inbound_text)
        )
        return FlowOutcome("needs_call", [], enrollment.appointment_slot, follow_up, created)

    async def _ensure_follow_up(
        self,
        enrollment: Enrollment,
        follow_up_type: FollowUpType,
        priority: FollowUpPriority,
    ) -> tuple[FollowUpItem, bool]:
        existing = await self._follow_ups.open_for_enrollment(enrollment.id)
        if existing is not None:
            existing.type = follow_up_type
            existing.priority = priority
            return existing, False
        item = FollowUpItem(
            enrollment_id=enrollment.id,
            type=follow_up_type,
            status=FollowUpStatus.OPEN,
            priority=priority,
        )
        await self._follow_ups.add_with_activity(
            item, FollowUpActivity(follow_up=item, action="created")
        )
        return item, True
