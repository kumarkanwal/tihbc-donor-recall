"""Database access for campaign enrollments."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.campaign import Campaign, Enrollment
from app.models.donor import Donor, Segment
from app.models.enums import EnrollmentStatus
from app.models.follow_up import FollowUpItem
from app.models.series import ContentSeries, SeriesStep
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class EnrollmentRecord:
    """Enrollment paired with its donor and segment."""

    enrollment: Enrollment
    donor: Donor
    segment_key: str


@dataclass(frozen=True)
class EnrollmentRecordPage:
    """One page of enrollment records."""

    items: tuple[EnrollmentRecord, ...]
    total: int
    page: int
    page_size: int


class EnrollmentRepository(BaseRepository[Enrollment]):
    """Query and persist enrollment aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Enrollment)

    async def add_many(self, enrollments: list[Enrollment]) -> None:
        """Add and flush launch enrollments in the current transaction."""
        self._session.add_all(enrollments)
        await self._session.flush()

    async def counts_by_status(self, campaign_id: UUID) -> dict[EnrollmentStatus, int]:
        """Count enrollments by status in one grouped query, including zero values."""
        counts = {status: 0 for status in EnrollmentStatus}
        rows = await self._session.execute(
            select(Enrollment.status, func.count(Enrollment.id))
            .where(Enrollment.campaign_id == campaign_id)
            .group_by(Enrollment.status)
        )
        counts.update({status: count for status, count in rows})
        return counts

    async def list_for_campaign(
        self,
        campaign_id: UUID,
        *,
        status: EnrollmentStatus | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> EnrollmentRecordPage:
        """Return filtered campaign enrollments with donor context."""
        filters = _filters(campaign_id, status, search)
        statement = (
            select(Enrollment, Donor, Segment.key)
            .join(Donor, Enrollment.donor_id == Donor.id)
            .join(Segment, Donor.segment_id == Segment.id)
            .where(*filters)
            .order_by(Donor.full_name, Enrollment.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = (
            select(func.count())
            .select_from(Enrollment)
            .join(Donor, Enrollment.donor_id == Donor.id)
            .join(Segment, Donor.segment_id == Segment.id)
            .where(*filters)
        )
        rows = await self._session.execute(statement)
        total = await self._session.scalar(count_statement)
        return EnrollmentRecordPage(
            items=tuple(
                EnrollmentRecord(enrollment=item, donor=donor, segment_key=segment)
                for item, donor, segment in rows
            ),
            total=total or 0,
            page=page,
            page_size=page_size,
        )

    async def get_full(self, enrollment_id: UUID) -> Enrollment | None:
        """Load one enrollment with donor, timeline, follow-up, and campaign."""
        statement = (
            select(Enrollment)
            .where(Enrollment.id == enrollment_id)
            .options(
                selectinload(Enrollment.campaign),
                selectinload(Enrollment.donor).selectinload(Donor.segment),
                selectinload(Enrollment.messages),
                selectinload(Enrollment.responses),
                selectinload(Enrollment.follow_up_items).selectinload(FollowUpItem.activities),
                selectinload(Enrollment.appointment_slot),
            )
        )
        return await self._session.scalar(statement)

    async def get_for_messaging_update(self, enrollment_id: UUID) -> Enrollment | None:
        """Lock an enrollment and load everything needed to render its next step."""
        primary_series = selectinload(Enrollment.campaign).selectinload(Campaign.primary_series)
        secondary_series = selectinload(Enrollment.campaign).selectinload(Campaign.secondary_series)
        statement = (
            select(Enrollment)
            .where(Enrollment.id == enrollment_id)
            .with_for_update()
            .execution_options(populate_existing=True)
            .options(
                selectinload(Enrollment.donor),
                selectinload(Enrollment.appointment_slot),
                primary_series.selectinload(ContentSeries.steps).selectinload(SeriesStep.contents),
                secondary_series.selectinload(ContentSeries.steps).selectinload(
                    SeriesStep.contents
                ),
            )
        )
        return await self._session.scalar(statement)


def _filters(
    campaign_id: UUID,
    status: EnrollmentStatus | None,
    search: str | None,
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = [Enrollment.campaign_id == campaign_id]
    if status is not None:
        filters.append(Enrollment.status == status)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filters.append(or_(Donor.full_name.ilike(term), Donor.phone_e164.ilike(term)))
    return filters
