"""Tests for donor upload field validation."""

from datetime import date
from uuid import uuid4

import pytest

from app.models.enums import LanguageCode
from app.services.batch_upload.parser import ParsedRow
from app.services.batch_upload.validators import (
    FieldValidationError,
    SegmentValue,
    find_duplicate_phone_rows,
    validate_blood_group,
    validate_city,
    validate_language,
    validate_last_donation_date,
    validate_name,
    validate_phone,
    validate_row,
    validate_segment,
)


@pytest.mark.parametrize(
    "raw_phone",
    ["0300-1234567", "+92 300 1234567", "923001234567"],
)
def test_phone_normalizes_supported_pakistani_mobile_formats(raw_phone: str) -> None:
    assert validate_phone(raw_phone) == "+923001234567"


@pytest.mark.parametrize(
    "raw_phone",
    ["021-12345678", "+1 202 555 0123", "0300-12345", ""],
)
def test_phone_rejects_non_pakistani_mobile_numbers(raw_phone: str) -> None:
    with pytest.raises(FieldValidationError, match="Invalid Pakistani mobile"):
        validate_phone(raw_phone)


def test_segment_accepts_key_and_label_case_insensitively() -> None:
    segment = SegmentValue(id=uuid4(), key="first_time")
    lookup = {"first_time": segment, "first time": segment}

    assert validate_segment(" FIRST_TIME ", lookup) == segment
    assert validate_segment("First Time", lookup) == segment


def test_segment_rejects_unknown_value() -> None:
    with pytest.raises(FieldValidationError, match="Unknown donor segment"):
        validate_segment("vip", {})


@pytest.mark.parametrize(
    ("raw_language", "expected"),
    [
        ("en", LanguageCode.EN),
        ("English", LanguageCode.EN),
        ("ur", LanguageCode.UR),
        ("URDU", LanguageCode.UR),
    ],
)
def test_language_normalizes_supported_values(raw_language: str, expected: LanguageCode) -> None:
    assert validate_language(raw_language) == expected


def test_language_rejects_unknown_value() -> None:
    with pytest.raises(FieldValidationError, match="Language must"):
        validate_language("Punjabi")


def test_optional_blood_group_and_date_validation() -> None:
    assert validate_blood_group("") is None
    assert validate_blood_group(" ab- ") == "AB-"
    assert validate_last_donation_date("15/01/2026", today=date(2026, 10, 3)) == date(2026, 1, 15)
    assert validate_last_donation_date("2026-01-15", today=date(2026, 10, 3)) == date(2026, 1, 15)


def test_invalid_blood_group_and_future_date_are_rejected() -> None:
    with pytest.raises(FieldValidationError, match="Invalid blood group"):
        validate_blood_group("A")
    with pytest.raises(FieldValidationError, match="future"):
        validate_last_donation_date("2026-10-04", today=date(2026, 10, 3))
    with pytest.raises(FieldValidationError, match="Invalid last donation date"):
        validate_last_donation_date("not-a-date", today=date(2026, 10, 3))


def test_name_is_required_and_trimmed() -> None:
    assert validate_name("  Fatima Ahmed  ") == "Fatima Ahmed"
    with pytest.raises(FieldValidationError, match="required"):
        validate_name("   ")


def test_optional_city_is_trimmed_and_length_limited() -> None:
    assert validate_city("") is None
    assert validate_city("  Karachi  ") == "Karachi"
    with pytest.raises(FieldValidationError, match="80 characters"):
        validate_city("x" * 81)


def test_duplicate_phone_keeps_first_row_and_rejects_later_row() -> None:
    rows = (
        ParsedRow(2, _row(phone="0300-1234567")),
        ParsedRow(3, _row(phone="+92 300 1234567")),
    )
    duplicate_rows = find_duplicate_phone_rows(rows)
    segment = SegmentValue(id=uuid4(), key="regular")

    first_donor, first_issues = validate_row(
        rows[0],
        segments={"regular": segment},
        duplicate_phone_rows=duplicate_rows,
        today=date(2026, 10, 3),
    )
    later_donor, later_issues = validate_row(
        rows[1],
        segments={"regular": segment},
        duplicate_phone_rows=duplicate_rows,
        today=date(2026, 10, 3),
    )

    assert first_donor is not None
    assert first_issues == []
    assert later_donor is None
    assert [(issue.field, issue.reason) for issue in later_issues] == [
        ("phone", "Duplicate of row 2")
    ]


def _row(*, phone: str) -> dict[str, str]:
    return {
        "name": "Ahsan Khan",
        "phone": phone,
        "segment": "regular",
        "language": "en",
        "city": "Karachi",
        "blood_group": "O+",
        "last_donation_date": "2026-01-15",
    }
