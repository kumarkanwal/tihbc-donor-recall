"""Database claims for concurrent scheduler ticks."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, Enrollment
from app.models.enums import CampaignStatus, EnrollmentStatus

DUE_ENROLLMENT_STATUSES = (
    EnrollmentStatus.PENDING,
    EnrollmentStatus.IN_PRIMARY,
    EnrollmentStatus.IN_SECONDARY,
)
FINAL_ENROLLMENT_STATUSES = (
    EnrollmentStatus.ESCALATED,
    EnrollmentStatus.CONFIRMED,
    EnrollmentStatus.RESCHEDULED,
    EnrollmentStatus.DECLINED,
    EnrollmentStatus.INVALID_NUMBER,
    EnrollmentStatus.UNDELIVERABLE,
)


class SchedulerRepository:
    """Claim one schedulable row at a time with skip-locked semantics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def next_scheduled_campaign(
        self,
        now: datetime,
        excluded_ids: frozenset[UUID],
    ) -> UUID | None:
        """Lock and return the next due scheduled campaign."""
        statement = (
            select(Campaign.id)
            .where(
                Campaign.status == CampaignStatus.SCHEDULED,
                Campaign.start_at <= now,
            )
            .order_by(Campaign.start_at, Campaign.id)
            .with_for_update(of=Campaign, skip_locked=True)
            .limit(1)
        )
        if excluded_ids:
            statement = statement.where(Campaign.id.not_in(excluded_ids))
        return await self._session.scalar(statement)

    async def next_due_enrollment(
        self,
        now: datetime,
        excluded_ids: frozenset[UUID],
    ) -> UUID | None:
        """Lock and return the next due enrollment in a running campaign."""
        statement = (
            select(Enrollment.id)
            .join(Campaign, Enrollment.campaign_id == Campaign.id)
            .where(
                Campaign.status == CampaignStatus.RUNNING,
                Enrollment.status.in_(DUE_ENROLLMENT_STATUSES),
                Enrollment.responded_at.is_(None),
                Enrollment.next_action_at.is_not(None),
                Enrollment.next_action_at <= now,
            )
            .order_by(Enrollment.next_action_at, Enrollment.id)
            .with_for_update(of=Enrollment, skip_locked=True)
            .limit(1)
        )
        if excluded_ids:
            statement = statement.where(Enrollment.id.not_in(excluded_ids))
        return await self._session.scalar(statement)

    async def next_completable_campaign(
        self,
        excluded_ids: frozenset[UUID],
    ) -> UUID | None:
        """Lock a running campaign whose enrollments are all final."""
        has_enrollments = exists(select(Enrollment.id).where(Enrollment.campaign_id == Campaign.id))
        has_non_final = exists(
            select(Enrollment.id).where(
                Enrollment.campaign_id == Campaign.id,
                Enrollment.status.not_in(FINAL_ENROLLMENT_STATUSES),
            )
        )
        statement = (
            select(Campaign.id)
            .where(
                Campaign.status == CampaignStatus.RUNNING,
                has_enrollments,
                ~has_non_final,
            )
            .order_by(Campaign.id)
            .with_for_update(of=Campaign, skip_locked=True)
            .limit(1)
        )
        if excluded_ids:
            statement = statement.where(Campaign.id.not_in(excluded_ids))
        return await self._session.scalar(statement)
