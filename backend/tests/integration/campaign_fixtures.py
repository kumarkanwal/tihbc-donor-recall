"""PostgreSQL fixture builders for campaign integration tests."""

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import LanguageCode, SeriesKind, SeriesStatus, UserRole
from app.models.series import ContentSeries
from app.models.user import User


@dataclass(frozen=True)
class CampaignFixture:
    """Persisted campaign prerequisites."""

    user: User
    batch: DonorBatch
    primary: ContentSeries
    secondary: ContentSeries
    donors: tuple[Donor, ...]


async def add_campaign_fixture(
    session: AsyncSession,
    *,
    donor_languages: tuple[LanguageCode, ...] = (
        LanguageCode.EN,
        LanguageCode.UR,
        LanguageCode.EN,
    ),
    series_status: SeriesStatus = SeriesStatus.ACTIVE,
) -> CampaignFixture:
    """Create unique batch, donors, and matching bilingual series."""
    token = uuid4().hex
    user = User(
        email=f"campaign-{token}@example.test",
        full_name="Campaign Admin",
        password_hash="test-hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    batch = DonorBatch(
        name=f"Campaign Batch {token}",
        original_filename="campaign.csv",
        uploaded_by=user,
        total_rows=len(donor_languages),
        valid_rows=len(donor_languages),
        invalid_rows=0,
        validation_report=[],
    )
    primary = _series(token, "Primary", SeriesKind.PRIMARY, series_status, user)
    secondary = _series(token, "Secondary", SeriesKind.SECONDARY, series_status, user)
    session.add_all((user, batch, primary, secondary))
    await session.flush()
    segment = await session.scalar(select(Segment).where(Segment.key == "regular"))
    assert segment is not None
    phone_suffix = int(token[:8], 16) % 10_000_000
    donors = tuple(
        Donor(
            batch=batch,
            full_name=f"Campaign Donor {index}",
            phone_e164=f"+923{index:02d}{phone_suffix:07d}",
            segment=segment,
            language=language,
            city="Karachi",
            blood_group="O+",
        )
        for index, language in enumerate(donor_languages)
    )
    session.add_all(donors)
    await session.flush()
    return CampaignFixture(user, batch, primary, secondary, donors)


def _series(
    token: str,
    label: str,
    kind: SeriesKind,
    status: SeriesStatus,
    user: User,
) -> ContentSeries:
    return ContentSeries(
        name=f"{label} {token}",
        kind=kind,
        status=status,
        languages=[LanguageCode.EN, LanguageCode.UR],
        created_by=user,
    )
