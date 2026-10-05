"""Default appointment calculation and capacity-safe booking."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.errors import ConflictError, NotFoundError
from app.models.campaign import AppointmentSlot, Enrollment
from app.repositories.appointment import AppointmentRepository
from app.services.appointments.centers import center_for_city

DEFAULT_APPOINTMENT_HOUR = 10
DEFAULT_APPOINTMENT_DAY_OFFSET = 2
BOOKING_WINDOW_DAYS = 2


class AppointmentService:
    """Book the default or next available donor appointment."""

    def __init__(self, repository: AppointmentRepository, timezone_display: str) -> None:
        self._repository = repository
        self._timezone = ZoneInfo(timezone_display)

    async def book_default(self, enrollment: Enrollment) -> AppointmentSlot:
        """Book once, honoring slot capacity under a row lock."""
        if enrollment.appointment_slot is not None:
            return enrollment.appointment_slot
        if enrollment.appointment_slot_id is not None:
            existing = await self._repository.get_slot(enrollment.appointment_slot_id)
            if existing is None:
                raise NotFoundError("Enrollment appointment slot not found")
            return existing
        target = default_appointment_start(enrollment.campaign.start_at, self._timezone)
        window_end = _following_day_end(target, self._timezone)
        slot = await self._repository.next_available_for_update(
            center_name=center_for_city(enrollment.donor.city),
            starts_at=target,
            before=window_end,
        )
        if slot is None:
            raise ConflictError("No appointment slots are available for this donor")
        slot.booked_count += 1
        enrollment.appointment_slot = slot
        return slot


def default_appointment_start(campaign_start: datetime, timezone: ZoneInfo) -> datetime:
    """Return campaign local date plus two days at 10:00, stored in UTC."""
    local_start = campaign_start.astimezone(timezone)
    appointment_date = local_start.date() + timedelta(days=DEFAULT_APPOINTMENT_DAY_OFFSET)
    return datetime.combine(
        appointment_date,
        time(hour=DEFAULT_APPOINTMENT_HOUR),
        tzinfo=timezone,
    ).astimezone(UTC)


def _following_day_end(target: datetime, timezone: ZoneInfo) -> datetime:
    local_date = target.astimezone(timezone).date()
    return datetime.combine(
        local_date + timedelta(days=BOOKING_WINDOW_DAYS),
        time.min,
        tzinfo=timezone,
    ).astimezone(UTC)
