"""Field-level donor upload validation and normalization."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

import phonenumbers
from phonenumbers import PhoneNumberFormat, PhoneNumberType

from app.models.enums import LanguageCode
from app.schemas.donor_batch import StoredDonorRow, ValidationIssue
from app.services.batch_upload.parser import ParsedRow

ALLOWED_BLOOD_GROUPS = frozenset({"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"})
DATE_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S")


class FieldValidationError(ValueError):
    """One donor field failed normalization."""


@dataclass(frozen=True)
class SegmentValue:
    """Canonical segment identity used during validation."""

    id: UUID
    key: str


def validate_name(value: str) -> str:
    """Normalize a required donor name."""
    normalized = value.strip()
    if not normalized:
        raise FieldValidationError("Name is required")
    if len(normalized) > 120:
        raise FieldValidationError("Name must be 120 characters or fewer")
    return normalized


def validate_phone(value: str) -> str:
    """Normalize one Pakistani mobile number to E.164."""
    normalized_input = value.strip()
    if normalized_input.startswith("92") and not normalized_input.startswith("+"):
        normalized_input = f"+{normalized_input}"
    try:
        number = phonenumbers.parse(normalized_input, "PK")
    except phonenumbers.NumberParseException as error:
        raise FieldValidationError("Invalid Pakistani mobile number") from error
    formatted = phonenumbers.format_number(number, PhoneNumberFormat.E164)
    if (
        not phonenumbers.is_valid_number(number)
        or phonenumbers.region_code_for_number(number) != "PK"
        or phonenumbers.number_type(number) != PhoneNumberType.MOBILE
        or not formatted.startswith("+923")
        or len(formatted) != 13
    ):
        raise FieldValidationError("Invalid Pakistani mobile number")
    return formatted


def validate_segment(value: str, segments: Mapping[str, SegmentValue]) -> SegmentValue:
    """Resolve a segment key or label case-insensitively."""
    segment = segments.get(value.strip().casefold())
    if segment is None:
        raise FieldValidationError("Unknown donor segment")
    return segment


def validate_language(value: str) -> LanguageCode:
    """Normalize supported language names and codes."""
    normalized = value.strip().casefold()
    aliases = {
        "en": LanguageCode.EN,
        "english": LanguageCode.EN,
        "ur": LanguageCode.UR,
        "urdu": LanguageCode.UR,
    }
    language = aliases.get(normalized)
    if language is None:
        raise FieldValidationError("Language must be English, Urdu, en, or ur")
    return language


def validate_blood_group(value: str) -> str | None:
    """Normalize an optional blood group."""
    normalized = value.strip().upper()
    if not normalized:
        return None
    if normalized not in ALLOWED_BLOOD_GROUPS:
        raise FieldValidationError("Invalid blood group")
    return normalized


def validate_last_donation_date(value: str, *, today: date) -> date | None:
    """Parse an optional common date format and reject future dates."""
    normalized = value.strip()
    if not normalized:
        return None
    parsed = _parse_date(normalized)
    if parsed is None:
        raise FieldValidationError("Invalid last donation date")
    if parsed > today:
        raise FieldValidationError("Last donation date cannot be in the future")
    return parsed


def validate_city(value: str) -> str | None:
    """Normalize an optional city."""
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > 80:
        raise FieldValidationError("City must be 80 characters or fewer")
    return normalized


def find_duplicate_phone_rows(rows: tuple[ParsedRow, ...]) -> dict[int, int]:
    """Map each later duplicate row to its first normalized phone row."""
    first_rows: dict[str, int] = {}
    duplicate_rows: dict[int, int] = {}
    for row in rows:
        try:
            phone = validate_phone(row.values["phone"])
        except FieldValidationError:
            continue
        first_row = first_rows.get(phone)
        if first_row is None:
            first_rows[phone] = row.row_number
            continue
        duplicate_rows[row.row_number] = first_row
    return duplicate_rows


def validate_row(
    row: ParsedRow,
    *,
    segments: Mapping[str, SegmentValue],
    duplicate_phone_rows: Mapping[int, int],
    today: date,
) -> tuple[StoredDonorRow | None, list[ValidationIssue]]:
    """Validate all supported fields in one donor row."""
    issues: list[ValidationIssue] = []
    name = _validated(row, "name", validate_name, issues)
    phone = _validated(row, "phone", validate_phone, issues)
    segment = _validated_segment(row, segments, issues)
    language = _validated(row, "language", validate_language, issues)
    city = _validated(row, "city", validate_city, issues)
    blood_group = _validated(row, "blood_group", validate_blood_group, issues)
    last_donation_date = _validated_date(row, today, issues)
    first_phone_row = duplicate_phone_rows.get(row.row_number)
    if phone is not None and first_phone_row is not None:
        issues.append(_issue(row, "phone", f"Duplicate of row {first_phone_row}"))
    if issues:
        return None, issues
    if name is None or phone is None or segment is None or language is None:
        raise RuntimeError("Required donor fields were not validated")
    return (
        StoredDonorRow(
            row=row.row_number,
            name=name,
            phone=phone,
            segment=segment.key,
            segment_id=segment.id,
            language=language,
            city=city,
            blood_group=blood_group,
            last_donation_date=last_donation_date,
        ),
        issues,
    )


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    return None


def _issue(row: ParsedRow, field: str, reason: str) -> ValidationIssue:
    return ValidationIssue(
        row=row.row_number,
        field=field,
        value=row.values.get(field, ""),
        reason=reason,
    )


def _validated[ValueType](
    row: ParsedRow,
    field: str,
    validator: Callable[[str], ValueType],
    issues: list[ValidationIssue],
) -> ValueType | None:
    try:
        return validator(row.values.get(field, ""))
    except FieldValidationError as error:
        issues.append(_issue(row, field, str(error)))
        return None


def _validated_segment(
    row: ParsedRow,
    segments: Mapping[str, SegmentValue],
    issues: list[ValidationIssue],
) -> SegmentValue | None:
    try:
        return validate_segment(row.values["segment"], segments)
    except FieldValidationError as error:
        issues.append(_issue(row, "segment", str(error)))
        return None


def _validated_date(
    row: ParsedRow,
    today: date,
    issues: list[ValidationIssue],
) -> date | None:
    try:
        return validate_last_donation_date(row.values.get("last_donation_date", ""), today=today)
    except FieldValidationError as error:
        issues.append(_issue(row, "last_donation_date", str(error)))
        return None
