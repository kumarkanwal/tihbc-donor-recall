"""Create demo campaigns, enrollments, and appointment assignments."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import AppointmentSlot, Campaign, Enrollment
from app.models.donor import Donor, DonorBatch
from app.models.enums import CampaignStatus, EnrollmentStatus, SeriesKind
from app.models.series import ContentSeries
from app.models.user import User
from app.seed.donors import SeedBatches


@dataclass(frozen=True)
class SeedCampaigns:
    """Seeded campaigns and live enrollment collections."""

    regular: Campaign
    lapsed: Campaign
    draft: Campaign
    regular_enrollments: tuple[Enrollment, ...]
    lapsed_enrollments: tuple[Enrollment, ...]


async def seed_campaigns(
    session: AsyncSession,
    batches: SeedBatches,
    series: dict[str, ContentSeries],
    admin: User,
    now: datetime,
) -> SeedCampaigns:
    """Persist two running campaigns and one launch-ready draft."""
    secondary = series["Final Follow-up"]
    regular = _campaign(
        "October Regular Recall",
        batches.regular,
        series["Regular Donor Recall"],
        secondary,
        admin,
        now - timedelta(days=10),
        CampaignStatus.RUNNING,
        now,
    )
    lapsed = _campaign(
        "Lapsed Donor Win-back",
        batches.lapsed,
        series["Lapsed Donor Win-back"],
        secondary,
        admin,
        now - timedelta(days=8),
        CampaignStatus.RUNNING,
        now,
    )
    draft = _campaign(
        "Duplicate Batch Test",
        batches.first_time,
        series["First-Time Donor Return"],
        secondary,
        admin,
        now + timedelta(days=1),
        CampaignStatus.DRAFT,
        now,
    )
    session.add_all((regular, lapsed, draft))
    await session.flush()

    slots = list(
        await session.scalars(
            select(AppointmentSlot).order_by(
                AppointmentSlot.starts_at,
                AppointmentSlot.center_name,
                AppointmentSlot.id,
            )
        )
    )
    regular_enrollments = _enrollments(
        regular,
        batches.regular_donors,
        slots,
        now,
        profile="regular",
    )
    lapsed_enrollments = _enrollments(
        lapsed,
        batches.lapsed_donors,
        slots,
        now,
        profile="lapsed",
    )
    session.add_all((*regular_enrollments, *lapsed_enrollments))
    await session.flush()
    return SeedCampaigns(
        regular,
        lapsed,
        draft,
        regular_enrollments,
        lapsed_enrollments,
    )


def _campaign(
    name: str,
    batch: DonorBatch,
    primary: ContentSeries,
    secondary: ContentSeries,
    admin: User,
    start_at: datetime,
    status: CampaignStatus,
    now: datetime,
) -> Campaign:
    return Campaign(
        name=name,
        batch=batch,
        primary_series=primary,
        secondary_series=secondary,
        status=status,
        start_at=start_at,
        launched_at=start_at if status == CampaignStatus.RUNNING else None,
        created_by=admin,
        created_at=start_at if status == CampaignStatus.RUNNING else now,
        updated_at=now,
    )


def _enrollments(
    campaign: Campaign,
    donors: tuple[Donor, ...],
    slots: list[AppointmentSlot],
    now: datetime,
    *,
    profile: str,
) -> tuple[Enrollment, ...]:
    enrollments: list[Enrollment] = []
    for index, donor in enumerate(donors):
        status = _status(profile, index, donor.sim_reachable)
        appointment = _reserve_slot(slots, index) if donor.sim_reachable else None
        responded = status in {
            EnrollmentStatus.CONFIRMED,
            EnrollmentStatus.RESCHEDULED,
            EnrollmentStatus.DECLINED,
        }
        secondary = status in {EnrollmentStatus.IN_SECONDARY, EnrollmentStatus.ESCALATED}
        enrollment = Enrollment(
            campaign=campaign,
            donor=donor,
            status=status,
            current_series_kind=SeriesKind.SECONDARY if secondary else SeriesKind.PRIMARY,
            current_step_order=_current_step(status),
            next_action_at=(
                now + timedelta(hours=12 + index % 36)
                if status in {EnrollmentStatus.IN_PRIMARY, EnrollmentStatus.IN_SECONDARY}
                else None
            ),
            responded_at=now - timedelta(days=index % 6, hours=2) if responded else None,
            appointment_slot=appointment,
            created_at=campaign.start_at,
            updated_at=now - timedelta(hours=index % 12),
        )
        enrollments.append(enrollment)
    return tuple(enrollments)


def _status(profile: str, index: int, reachable: bool) -> EnrollmentStatus:
    if not reachable:
        return EnrollmentStatus.UNDELIVERABLE
    boundaries = (25, 40, 55, 65, 85, 95) if profile == "regular" else (12, 22, 32, 42, 52, 60)
    statuses = (
        EnrollmentStatus.CONFIRMED,
        EnrollmentStatus.RESCHEDULED,
        EnrollmentStatus.DECLINED,
        EnrollmentStatus.ESCALATED,
        EnrollmentStatus.IN_PRIMARY,
        EnrollmentStatus.IN_SECONDARY,
    )
    for boundary, status in zip(boundaries, statuses, strict=True):
        if index < boundary:
            return status
    return EnrollmentStatus.IN_SECONDARY


def _current_step(status: EnrollmentStatus) -> int:
    if status == EnrollmentStatus.IN_PRIMARY:
        return 2
    if status in {EnrollmentStatus.IN_SECONDARY, EnrollmentStatus.ESCALATED}:
        return 1 if status == EnrollmentStatus.IN_SECONDARY else 2
    return 1


def _reserve_slot(slots: list[AppointmentSlot], donor_index: int) -> AppointmentSlot | None:
    for offset in range(len(slots)):
        slot = slots[(donor_index * 3 + offset) % len(slots)]
        if slot.booked_count < slot.capacity:
            slot.booked_count += 1
            return slot
    return None
