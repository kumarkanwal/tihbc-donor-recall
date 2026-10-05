"""Enrollment state transitions owned by deterministic reply handling."""

from app.core.errors import InvalidStateTransitionError
from app.models.campaign import Enrollment
from app.models.enums import EnrollmentStatus

REPLY_TRANSITIONS: dict[EnrollmentStatus, frozenset[EnrollmentStatus]] = {
    EnrollmentStatus.PENDING: frozenset(
        {
            EnrollmentStatus.CONFIRMED,
            EnrollmentStatus.RESCHEDULE_REQUESTED,
            EnrollmentStatus.DECLINED,
        }
    ),
    EnrollmentStatus.IN_PRIMARY: frozenset(
        {
            EnrollmentStatus.CONFIRMED,
            EnrollmentStatus.RESCHEDULE_REQUESTED,
            EnrollmentStatus.DECLINED,
        }
    ),
    EnrollmentStatus.IN_SECONDARY: frozenset(
        {
            EnrollmentStatus.CONFIRMED,
            EnrollmentStatus.RESCHEDULE_REQUESTED,
            EnrollmentStatus.DECLINED,
        }
    ),
    EnrollmentStatus.ESCALATED: frozenset(
        {
            EnrollmentStatus.CONFIRMED,
            EnrollmentStatus.RESCHEDULE_REQUESTED,
            EnrollmentStatus.DECLINED,
        }
    ),
    EnrollmentStatus.CONFIRMED: frozenset(
        {EnrollmentStatus.RESCHEDULE_REQUESTED, EnrollmentStatus.DECLINED}
    ),
    EnrollmentStatus.RESCHEDULE_REQUESTED: frozenset(
        {
            EnrollmentStatus.CONFIRMED,
            EnrollmentStatus.RESCHEDULED,
            EnrollmentStatus.DECLINED,
        }
    ),
    EnrollmentStatus.RESCHEDULED: frozenset(
        {EnrollmentStatus.RESCHEDULE_REQUESTED, EnrollmentStatus.DECLINED}
    ),
    EnrollmentStatus.DECLINED: frozenset(
        {EnrollmentStatus.CONFIRMED, EnrollmentStatus.RESCHEDULE_REQUESTED}
    ),
}


def transition_enrollment(enrollment: Enrollment, target: EnrollmentStatus) -> None:
    """Apply one valid reply-driven status change."""
    if enrollment.status == target:
        return
    if target not in REPLY_TRANSITIONS.get(enrollment.status, frozenset()):
        raise InvalidStateTransitionError(
            f"Enrollment cannot transition from {enrollment.status.value} to {target.value}",
            {"current": enrollment.status.value, "target": target.value},
        )
    enrollment.status = target
