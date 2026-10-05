"""Default appointment calculation and capacity-safe booking."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
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
        """Keep a future booking or replace a stale one under row locks."""
        now = self._clock.now()
        existing = await self._existing(enrollment)
        if existing is not None and existing.starts_at >= now:
            return existing
        if existing is not None:
            await self._release_stale(enrollment, existing)
        return await self._book_new(enrollment, now)

    async def _existing(self, enrollment: Enrollment) -> AppointmentSlot | None:
        if enrollment.appointment_slot is not None:
            return enrollment.appointment_slot
        if enrollment.appointment_slot_id is None:
            return None
        existing = await self._repository.get_slot(enrollment.appointment_slot_id)
        if existing is None:
            raise NotFoundError("Enrollment appointment slot not found")
        return existing

    async def _release_stale(self, enrollment: Enrollment, existing: AppointmentSlot) -> None:
        locked = await self._repository.get_for_update(existing.id)
        if locked is None:
            raise NotFoundError("Enrollment appointment slot not found")
        if locked.booked_count > 0:
            locked.booked_count -= 1
        enrollment.appointment_slot = None
        enrollment.appointment_slot_id = None

    async def _book_new(self, enrollment: Enrollment, now: datetime) -> AppointmentSlot | None:
        base = max(enrollment.campaign.start_at, now)
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

    async def offer(self, requested_date: date | None = None) -> tuple[AppointmentSlot, ...]:
        """Return up to three available slots nearest to the requested date."""
        starts_at = self._clock.now()
        if requested_date is not None:
            starts_at = datetime.combine(requested_date, time.min, self._timezone).astimezone(UTC)
        return await self._repository.available(
            starts_at=starts_at,
            before=starts_at + timedelta(days=SEARCH_FORWARD_DAYS + 1),
            limit=3,
        )

    async def book_selected(self, enrollment: Enrollment, slot_id: UUID) -> AppointmentSlot | None:
        """Book one selected slot under row locks, releasing a prior booking."""
        if enrollment.appointment_slot_id == slot_id:
            return enrollment.appointment_slot or await self._repository.get_slot(slot_id)
        selected = await self._repository.available_for_update(slot_id)
        if selected is None:
            return None
        if enrollment.appointment_slot_id is not None:
            previous = await self._repository.get_for_update(enrollment.appointment_slot_id)
            if previous is not None and previous.booked_count > 0:
                previous.booked_count -= 1
        selected.booked_count += 1
        enrollment.appointment_slot = selected
        return selected


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
