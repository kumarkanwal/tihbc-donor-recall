"""Default appointment calculation and capacity-safe booking."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import structlog

from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.models.campaign import AppointmentSlot, Enrollment
from app.repositories.appointment import AppointmentRepository
from app.services.appointments.centers import center_for_city

DEFAULT_APPOINTMENT_HOUR = 10
DEFAULT_APPOINTMENT_DAY_OFFSET = 2
SEARCH_FORWARD_DAYS = 14
logger = structlog.get_logger(__name__)


class AppointmentService:
    """Book the default or next available donor appointment."""

    def __init__(
        self,
        repository: AppointmentRepository,
        current_clock: Clock,
        timezone_display: str,
    ) -> None:
        self._repository = repository
        self._clock = current_clock
        self._timezone = ZoneInfo(timezone_display)

    async def book_default(self, enrollment: Enrollment) -> AppointmentSlot | None:
        """Book once under a row lock, or allow fallback text when no slot exists."""
        if enrollment.appointment_slot is not None:
            return enrollment.appointment_slot
        if enrollment.appointment_slot_id is not None:
            existing = await self._repository.get_slot(enrollment.appointment_slot_id)
            if existing is None:
                raise NotFoundError("Enrollment appointment slot not found")
            return existing
        base = max(enrollment.campaign.start_at, self._clock.now())
        target = default_appointment_start(base, self._timezone)
        window_end = _search_window_end(target, self._timezone)
        preferred_center = center_for_city(enrollment.donor.city)
        slot = await self._repository.next_available_for_update(
            center_name=preferred_center,
            starts_at=target,
            before=window_end,
        )
        if slot is None:
            slot = await self._repository.next_available_for_update(
                center_name=None,
                starts_at=target,
                before=window_end,
            )
        if slot is None:
            logger.warning(
                "appointment_slot_unavailable",
                enrollment_id=str(enrollment.id),
                campaign_id=str(enrollment.campaign_id),
                preferred_center=preferred_center,
                search_days=SEARCH_FORWARD_DAYS,
            )
            return None
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


def _search_window_end(target: datetime, timezone: ZoneInfo) -> datetime:
    local_date = target.astimezone(timezone).date()
    return datetime.combine(
        local_date + timedelta(days=SEARCH_FORWARD_DAYS + 1),
        time.min,
        tzinfo=timezone,
    ).astimezone(UTC)
