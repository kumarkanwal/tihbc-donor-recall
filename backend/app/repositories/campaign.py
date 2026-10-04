"""Database access for campaigns and enrollments."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement

from app.models.campaign import Campaign, Enrollment
from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import CampaignStatus, EnrollmentStatus, LanguageCode
from app.models.follow_up import FollowUpItem
from app.models.series import ContentSeries
from app.models.user import User
from app.repositories.base import BaseRepository

LIVE_CAMPAIGN_STATUSES = (
    CampaignStatus.SCHEDULED,
    CampaignStatus.RUNNING,
    CampaignStatus.PAUSED,
)


@dataclass(frozen=True)
class CampaignRecord:
    """Campaign and query-computed summary values."""

    campaign: Campaign
    batch_name: str
    primary_series_name: str
    secondary_series_name: str
    created_by: User
    enrollment_count: int
    responded_count: int


@dataclass(frozen=True)
class CampaignRecordPage:
    """One page of campaign summary records."""

    items: tuple[CampaignRecord, ...]
    total: int
    page: int
    page_size: int


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


class CampaignRepository(BaseRepository[Campaign]):
    """Query and persist campaign aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Campaign)

    async def list_filtered(
        self,
        *,
        status: CampaignStatus | None,
        page: int,
        page_size: int,
    ) -> CampaignRecordPage:
        """Return campaigns with relationship names and response totals."""
        filters = [Campaign.status == status] if status is not None else []
        statement = self._summary_statement(filters).offset((page - 1) * page_size).limit(page_size)
        rows = await self._session.execute(statement)
        total = await self._session.scalar(
            select(func.count()).select_from(Campaign).where(*filters)
        )
        return CampaignRecordPage(
            items=tuple(
                CampaignRecord(
                    campaign=campaign,
                    batch_name=batch_name,
                    primary_series_name=primary_name,
                    secondary_series_name=secondary_name,
                    created_by=user,
                    enrollment_count=enrolled,
                    responded_count=responded,
                )
                for (
                    campaign,
                    batch_name,
                    primary_name,
                    secondary_name,
                    user,
                    enrolled,
                    responded,
                ) in rows
            ),
            total=total or 0,
            page=page,
            page_size=page_size,
        )

    async def get_summary(self, campaign_id: UUID) -> CampaignRecord | None:
        """Return one campaign summary by identifier."""
        row = (
            await self._session.execute(self._summary_statement([Campaign.id == campaign_id]))
        ).one_or_none()
        if row is None:
            return None
        campaign, batch_name, primary_name, secondary_name, user, enrolled, responded = row
        return CampaignRecord(
            campaign=campaign,
            batch_name=batch_name,
            primary_series_name=primary_name,
            secondary_series_name=secondary_name,
            created_by=user,
            enrollment_count=enrolled,
            responded_count=responded,
        )

    async def get_full_for_update(self, campaign_id: UUID) -> Campaign | None:
        """Lock and load one campaign with its launch-validation relationships."""
        statement = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .with_for_update()
            .execution_options(populate_existing=True)
            .options(
                selectinload(Campaign.batch),
                selectinload(Campaign.primary_series),
                selectinload(Campaign.secondary_series),
            )
        )
        return await self._session.scalar(statement)

    async def lock_batch(self, batch_id: UUID) -> bool:
        """Lock one batch to serialize campaign launches for its donors."""
        statement = select(DonorBatch.id).where(DonorBatch.id == batch_id).with_for_update()
        return await self._session.scalar(statement) is not None

    async def get_batch(self, batch_id: UUID) -> DonorBatch | None:
        """Return a donor batch by identifier."""
        return await self._session.get(DonorBatch, batch_id)

    async def get_series(self, series_id: UUID) -> ContentSeries | None:
        """Return content series by identifier."""
        return await self._session.get(ContentSeries, series_id)

    async def donor_language_counts(self, batch_id: UUID) -> tuple[tuple[LanguageCode, int], ...]:
        """Return one donor count per language in a batch."""
        statement = (
            select(Donor.language, func.count(Donor.id))
            .where(Donor.batch_id == batch_id)
            .group_by(Donor.language)
            .order_by(Donor.language)
        )
        return tuple(
            (language, count) for language, count in await self._session.execute(statement)
        )

    async def donors_for_batch(self, batch_id: UUID) -> tuple[Donor, ...]:
        """Return every donor in deterministic order for enrollment creation."""
        donors = await self._session.scalars(
            select(Donor).where(Donor.batch_id == batch_id).order_by(Donor.id)
        )
        return tuple(donors.all())

    async def has_live_campaign_for_batch(
        self, batch_id: UUID, *, excluding_campaign_id: UUID
    ) -> bool:
        """Return whether another live campaign already uses the batch."""
        count = await self._session.scalar(
            select(func.count())
            .select_from(Campaign)
            .where(
                Campaign.batch_id == batch_id,
                Campaign.id != excluding_campaign_id,
                Campaign.status.in_(LIVE_CAMPAIGN_STATUSES),
            )
        )
        return bool(count)

    async def add_enrollments(self, enrollments: list[Enrollment]) -> None:
        """Add and flush launch enrollments in the current transaction."""
        self._session.add_all(enrollments)
        await self._session.flush()

    async def enrollment_counts(self, campaign_id: UUID) -> dict[EnrollmentStatus, int]:
        """Count enrollments by status in one grouped query, including zero values."""
        counts = {status: 0 for status in EnrollmentStatus}
        rows = await self._session.execute(
            select(Enrollment.status, func.count(Enrollment.id))
            .where(Enrollment.campaign_id == campaign_id)
            .group_by(Enrollment.status)
        )
        counts.update({status: count for status, count in rows})
        return counts

    async def list_enrollments(
        self,
        campaign_id: UUID,
        *,
        status: EnrollmentStatus | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> EnrollmentRecordPage:
        """Return filtered campaign enrollments with donor context."""
        filters = self._enrollment_filters(campaign_id, status, search)
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

    async def get_enrollment_full(self, enrollment_id: UUID) -> Enrollment | None:
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

    def _summary_statement(
        self, filters: list[ColumnElement[bool]]
    ) -> Select[tuple[Campaign, str, str, str, User, int, int]]:
        primary_series = aliased(ContentSeries)
        secondary_series = aliased(ContentSeries)
        return (
            select(
                Campaign,
                DonorBatch.name,
                primary_series.name,
                secondary_series.name,
                User,
                func.count(Enrollment.id),
                func.count(Enrollment.id).filter(Enrollment.responded_at.is_not(None)),
            )
            .join(DonorBatch, Campaign.batch_id == DonorBatch.id)
            .join(primary_series, Campaign.primary_series_id == primary_series.id)
            .join(secondary_series, Campaign.secondary_series_id == secondary_series.id)
            .join(User, Campaign.created_by_id == User.id)
            .outerjoin(Enrollment, Enrollment.campaign_id == Campaign.id)
            .where(*filters)
            .group_by(Campaign.id, DonorBatch.id, primary_series.id, secondary_series.id, User.id)
            .order_by(Campaign.created_at.desc(), Campaign.id)
        )

    @staticmethod
    def _enrollment_filters(
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
