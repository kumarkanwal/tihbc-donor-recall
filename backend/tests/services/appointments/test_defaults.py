"""Tests for default center and appointment calculation."""

from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from structlog.testing import capture_logs

from app.models.campaign import Enrollment
from app.repositories.appointment import AppointmentRepository
from app.services.appointments.centers import (
    KORANGI_CENTER,
    NORTH_NAZIMABAD_CENTER,
    center_for_city,
)
from app.services.appointments.service import AppointmentService, default_appointment_start
from tests.integration.messaging_fixtures import FixedClock


def test_center_selection_defaults_to_korangi() -> None:
    assert center_for_city("North Nazimabad") == NORTH_NAZIMABAD_CENTER
    assert center_for_city("Karachi") == KORANGI_CENTER
    assert center_for_city(None) == KORANGI_CENTER


def test_default_appointment_is_two_local_days_later_at_ten() -> None:
    campaign_start = datetime(2026, 10, 4, 20, 30, tzinfo=UTC)

    result = default_appointment_start(campaign_start, ZoneInfo("Asia/Karachi"))

    local = result.astimezone(ZoneInfo("Asia/Karachi"))
    assert local == datetime(2026, 10, 7, 10, 0, tzinfo=ZoneInfo("Asia/Karachi"))


@pytest.mark.asyncio
async def test_no_slot_in_search_window_returns_none() -> None:
    repository_mock = AsyncMock(spec=AppointmentRepository)
    repository_mock.next_available_for_update.side_effect = [None, None]
    service = AppointmentService(
        cast(AppointmentRepository, repository_mock),
        FixedClock(datetime(2026, 10, 4, 7, 0, tzinfo=UTC)),
        "Asia/Karachi",
    )
    enrollment_mock = MagicMock(spec=Enrollment)
    enrollment_mock.appointment_slot = None
    enrollment_mock.appointment_slot_id = None
    enrollment_mock.campaign.start_at = datetime(2026, 1, 1, tzinfo=UTC)
    enrollment_mock.donor.city = "Karachi"

    with capture_logs() as logs:
        result = await service.book_default(cast(Enrollment, enrollment_mock))

    assert result is None
    assert repository_mock.next_available_for_update.await_count == 2
    assert logs[-1]["event"] == "appointment_slot_unavailable"
    assert logs[-1]["log_level"] == "warning"
