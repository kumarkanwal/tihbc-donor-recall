"""Tests for default center and appointment calculation."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.services.appointments.centers import (
    KORANGI_CENTER,
    NORTH_NAZIMABAD_CENTER,
    center_for_city,
)
from app.services.appointments.service import default_appointment_start


def test_center_selection_defaults_to_korangi() -> None:
    assert center_for_city("North Nazimabad") == NORTH_NAZIMABAD_CENTER
    assert center_for_city("Karachi") == KORANGI_CENTER
    assert center_for_city(None) == KORANGI_CENTER


def test_default_appointment_is_two_local_days_later_at_ten() -> None:
    campaign_start = datetime(2026, 10, 4, 20, 30, tzinfo=UTC)

    result = default_appointment_start(campaign_start, ZoneInfo("Asia/Karachi"))

    local = result.astimezone(ZoneInfo("Asia/Karachi"))
    assert local == datetime(2026, 10, 7, 10, 0, tzinfo=ZoneInfo("Asia/Karachi"))
