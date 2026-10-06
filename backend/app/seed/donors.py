"""Deterministic demo donor, segment, and batch seed data."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import LanguageCode
from app.models.user import User

SEGMENT_COUNTS = {"regular": 100, "lapsed": 60, "first_time": 35}
SEGMENT_LABELS = {
    "regular": "Regular",
    "lapsed": "Lapsed",
    "first_time": "First Time",
}
BLOOD_GROUPS = ("O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-")
CITIES = ("Karachi", "Korangi", "North Nazimabad", "Gulshan-e-Iqbal", "Malir")
GIVEN_NAMES = (
    "Ahsan",
    "Fatima",
    "Bilal",
    "Ayesha",
    "Hamza",
    "Sana",
    "Usman",
    "Hira",
    "Ali",
    "Zainab",
    "Danish",
    "Maham",
    "Saad",
    "Iqra",
    "Fahad",
    "Mehwish",
    "Omer",
    "Rabia",
    "Hassan",
    "Nida",
    "Imran",
    "Kiran",
    "Salman",
    "Maryam",
    "Shahzaib",
    "Anum",
    "Talha",
    "Sidra",
    "Farhan",
    "Hafsa",
    "Noman",
    "Amna",
    "Waqas",
    "Laiba",
    "Adnan",
    "Komal",
    "Asad",
    "Madiha",
    "Rizwan",
    "Bushra",
)
FAMILY_NAMES = (
    "Khan",
    "Ahmed",
    "Ali",
    "Siddiqui",
    "Qureshi",
    "Sheikh",
    "Malik",
    "Raza",
    "Hussain",
    "Iqbal",
)


@dataclass(frozen=True)
class SeedBatches:
    """Seeded batch roots and their persisted valid donors."""

    regular: DonorBatch
    lapsed: DonorBatch
    first_time: DonorBatch
    regular_donors: tuple[Donor, ...]
    lapsed_donors: tuple[Donor, ...]
    first_time_donors: tuple[Donor, ...]


async def seed_batches_and_donors(
    session: AsyncSession,
    admin: User,
    now: datetime,
) -> SeedBatches:
    """Persist the documented segment mix across three campaign-ready batches."""
    segments = {
        key: Segment(key=key, label=label, created_at=now, updated_at=now)
        for key, label in SEGMENT_LABELS.items()
    }
    session.add_all(segments.values())
    await session.flush()

    regular = _batch("October Regular Donors", "regular-donors.xlsx", admin, 100, 0, now)
    lapsed = _batch("Lapsed Donor Win-back", "lapsed-donors.xlsx", admin, 60, 0, now)
    first_time = _batch(
        "First-Time Demo Upload",
        "sample-donors.xlsx",
        admin,
        40,
        5,
        now,
        validation_report=sample_validation_report(),
    )
    session.add_all((regular, lapsed, first_time))
    await session.flush()

    regular_donors = _donors(regular, segments["regular"], 0, 100, now)
    lapsed_donors = _donors(lapsed, segments["lapsed"], 100, 60, now)
    first_time_donors = _donors(first_time, segments["first_time"], 160, 35, now)
    session.add_all((*regular_donors, *lapsed_donors, *first_time_donors))
    await session.flush()
    return SeedBatches(
        regular,
        lapsed,
        first_time,
        regular_donors,
        lapsed_donors,
        first_time_donors,
    )


def sample_valid_rows() -> list[dict[str, str]]:
    """Return the 35 valid rows shared by the workbook and seeded upload batch."""
    return [_sample_row(index) for index in range(160, 195)]


def sample_invalid_rows() -> list[dict[str, str]]:
    """Return the five specifically documented invalid upload examples."""
    base = _sample_row(195)
    return [
        {**base, "name": "Kamran Yousaf", "phone": "12345"},
        {**base, "name": "Sehrish Noor", "phone": "+923001000196", "segment": "vip"},
        {**base, "name": "", "phone": "+923001000197"},
        {**base, "name": "Junaid Akram", "phone": "+923001000160"},
        {
            **base,
            "name": "Nadia Saleem",
            "phone": "+923001000199",
            "last_donation_date": "2099-01-01",
        },
    ]


def sample_validation_report() -> list[dict[str, object]]:
    """Return the stored validation report corresponding to sample invalid rows."""
    return [
        {
            "row": 37,
            "field": "phone",
            "value": "12345",
            "reason": "Invalid Pakistani mobile number",
        },
        {"row": 38, "field": "segment", "value": "vip", "reason": "Unknown donor segment"},
        {"row": 39, "field": "name", "value": "", "reason": "Name is required"},
        {"row": 40, "field": "phone", "value": "+923001000160", "reason": "Duplicate of row 2"},
        {
            "row": 41,
            "field": "last_donation_date",
            "value": "2099-01-01",
            "reason": "Last donation date cannot be in the future",
        },
    ]


def _batch(
    name: str,
    filename: str,
    admin: User,
    total_rows: int,
    invalid_rows: int,
    now: datetime,
    *,
    validation_report: list[dict[str, object]] | None = None,
) -> DonorBatch:
    return DonorBatch(
        name=name,
        original_filename=filename,
        uploaded_by=admin,
        total_rows=total_rows,
        valid_rows=total_rows - invalid_rows,
        invalid_rows=invalid_rows,
        validation_report=validation_report or [],
        created_at=now,
        updated_at=now,
    )


def _donors(
    batch: DonorBatch,
    segment: Segment,
    start_index: int,
    count: int,
    now: datetime,
) -> tuple[Donor, ...]:
    return tuple(
        Donor(
            batch=batch,
            full_name=_name(index),
            phone_e164=_phone(index),
            segment=segment,
            language=_language(index),
            city=CITIES[index % len(CITIES)],
            blood_group=BLOOD_GROUPS[index % len(BLOOD_GROUPS)],
            last_donation_date=(now - timedelta(days=120 + index % 500)).date(),
            sim_reachable=index % 20 != 0,
            sim_read_receipts=index % 4 != 0,
            created_at=now,
            updated_at=now,
        )
        for index in range(start_index, start_index + count)
    )


def _sample_row(index: int) -> dict[str, str]:
    return {
        "name": _name(index),
        "phone": _phone(index),
        "segment": "first_time",
        "language": _language(index).value,
        "city": CITIES[index % len(CITIES)],
        "blood_group": BLOOD_GROUPS[index % len(BLOOD_GROUPS)],
        "last_donation_date": "2025-12-01",
    }


def _name(index: int) -> str:
    given_name = GIVEN_NAMES[index % len(GIVEN_NAMES)]
    family_index = (index // len(GIVEN_NAMES)) % len(FAMILY_NAMES)
    return f"{given_name} {FAMILY_NAMES[family_index]}"


def _phone(index: int) -> str:
    return f"+92300{1_000_000 + index:07d}"


def _language(index: int) -> LanguageCode:
    return LanguageCode.UR if index % 5 < 3 else LanguageCode.EN
