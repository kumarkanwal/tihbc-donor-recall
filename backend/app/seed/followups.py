"""Build realistic coordinator follow-up history for seeded enrollments."""

from datetime import datetime, timedelta

from app.models.campaign import Enrollment
from app.models.enums import (
    EnrollmentStatus,
    FollowUpOutcome,
    FollowUpPriority,
    FollowUpStatus,
    FollowUpType,
)
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.models.user import User

FOLLOW_UP_TYPES = {
    EnrollmentStatus.CONFIRMED: FollowUpType.CONFIRMED,
    EnrollmentStatus.RESCHEDULED: FollowUpType.RESCHEDULE,
    EnrollmentStatus.DECLINED: FollowUpType.DECLINED,
    EnrollmentStatus.ESCALATED: FollowUpType.NEEDS_CALL,
}
FOLLOW_UP_STATUSES = (
    FollowUpStatus.OPEN,
    FollowUpStatus.IN_PROGRESS,
    FollowUpStatus.DONE,
)


def build_follow_up(
    enrollment: Enrollment,
    coordinator: User,
    index: int,
    now: datetime,
) -> FollowUpItem:
    """Return one auditable seeded follow-up for a terminal enrollment."""
    status = FOLLOW_UP_STATUSES[index % len(FOLLOW_UP_STATUSES)]
    created_at = enrollment.responded_at or now - timedelta(days=index % 5)
    is_done = status == FollowUpStatus.DONE
    item = FollowUpItem(
        enrollment=enrollment,
        type=FOLLOW_UP_TYPES[enrollment.status],
        status=status,
        priority=(
            FollowUpPriority.HIGH
            if enrollment.status == EnrollmentStatus.ESCALATED
            else FollowUpPriority.NORMAL
        ),
        assigned_to=coordinator if status != FollowUpStatus.OPEN else None,
        outcome=_outcome(enrollment.status) if is_done else None,
        resolved_at=created_at + timedelta(hours=3) if is_done else None,
        resolved_by=coordinator if is_done else None,
        created_at=created_at,
        updated_at=created_at + timedelta(hours=3) if is_done else created_at,
    )
    item.activities = [_activity(item, None, "created", None, created_at)]
    if status != FollowUpStatus.OPEN:
        item.activities.append(
            _activity(item, coordinator, "assigned", None, created_at + timedelta(hours=1))
        )
    if is_done:
        item.activities.append(
            _activity(
                item,
                coordinator,
                "resolved",
                "Follow-up completed during the demo history.",
                created_at + timedelta(hours=3),
            )
        )
    return item


def _activity(
    item: FollowUpItem,
    user: User | None,
    action: str,
    note: str | None,
    created_at: datetime,
) -> FollowUpActivity:
    return FollowUpActivity(
        follow_up=item,
        user=user,
        action=action,
        note=note,
        created_at=created_at,
        updated_at=created_at,
    )


def _outcome(status: EnrollmentStatus) -> FollowUpOutcome:
    return {
        EnrollmentStatus.CONFIRMED: FollowUpOutcome.ATTENDED,
        EnrollmentStatus.RESCHEDULED: FollowUpOutcome.REBOOKED,
        EnrollmentStatus.DECLINED: FollowUpOutcome.DECLINED,
        EnrollmentStatus.ESCALATED: FollowUpOutcome.NOT_REACHABLE,
    }[status]
