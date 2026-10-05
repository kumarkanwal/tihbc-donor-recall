"""Campaign creation and lifecycle mutations."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import InvalidStateTransitionError, NotFoundError, ValidationError
from app.models.campaign import Campaign, Enrollment
from app.models.enums import CampaignStatus, EnrollmentStatus, SeriesKind
from app.repositories.campaign import CampaignRepository
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.campaign import CampaignCreate, CampaignDetail, CampaignUpdate
from app.schemas.user import UserOut
from app.services.campaigns.mappers import campaign_detail
from app.services.campaigns.transitions import (
    require_campaign_status,
    transition_campaign,
    validate_campaign_transition,
)
from app.services.campaigns.validation import launch_problems
from app.services.events.base import EventPublisher
from app.services.events.logging import LoggingEventPublisher
from app.ws.events import EventType


class CampaignService:
    """Own campaign writes, validation, transitions, and transactions."""

    def __init__(
        self,
        session: AsyncSession,
        campaign_repository: CampaignRepository,
        enrollment_repository: EnrollmentRepository,
        current_clock: Clock,
        publisher: EventPublisher | None = None,
    ) -> None:
        self._session = session
        self._campaigns = campaign_repository
        self._enrollments = enrollment_repository
        self._clock = current_clock
        self._publisher = publisher or LoggingEventPublisher()

    async def create(self, request: CampaignCreate, created_by: UserOut) -> CampaignDetail:
        """Create one campaign in draft status."""
        await self._require_references(
            request.batch_id,
            request.primary_series_id,
            request.secondary_series_id,
        )
        campaign = Campaign(
            name=request.name,
            batch_id=request.batch_id,
            primary_series_id=request.primary_series_id,
            secondary_series_id=request.secondary_series_id,
            status=CampaignStatus.DRAFT,
            start_at=request.start_at,
            created_by_id=created_by.id,
        )
        await self._campaigns.add(campaign)
        await self._commit()
        return await self._detail(campaign.id)

    async def update(self, campaign_id: UUID, request: CampaignUpdate) -> CampaignDetail:
        """Update selected fields on a draft campaign."""
        campaign = await self._required_locked(campaign_id)
        require_campaign_status(campaign, CampaignStatus.DRAFT, "edit")
        fields = request.model_fields_set
        batch_id = request.batch_id if request.batch_id is not None else campaign.batch_id
        primary_id = (
            request.primary_series_id
            if request.primary_series_id is not None
            else campaign.primary_series_id
        )
        secondary_id = (
            request.secondary_series_id
            if request.secondary_series_id is not None
            else campaign.secondary_series_id
        )
        await self._require_references(batch_id, primary_id, secondary_id)
        if request.name is not None:
            campaign.name = request.name
        if "batch_id" in fields:
            campaign.batch_id = batch_id
        if "primary_series_id" in fields:
            campaign.primary_series_id = primary_id
        if "secondary_series_id" in fields:
            campaign.secondary_series_id = secondary_id
        if request.start_at is not None:
            campaign.start_at = request.start_at
        await self._commit()
        return await self._detail(campaign.id)

    async def launch(self, campaign_id: UUID) -> CampaignDetail:
        """Validate and launch a draft campaign, creating all enrollments."""
        campaign = await self._required_locked(campaign_id)
        now = self._clock.now()
        target = CampaignStatus.SCHEDULED if campaign.start_at > now else CampaignStatus.RUNNING
        validate_campaign_transition(campaign.status, target)
        await self._campaigns.lock_batch(campaign.batch_id)
        donor_language_counts = await self._campaigns.donor_language_counts(campaign.batch_id)
        batch_has_live_campaign = await self._campaigns.has_live_campaign_for_batch(
            campaign.batch_id,
            excluding_campaign_id=campaign.id,
        )
        problems = launch_problems(
            campaign,
            donor_language_counts,
            batch_has_live_campaign=batch_has_live_campaign,
        )
        if problems:
            raise ValidationError(
                "Campaign cannot be launched",
                {"problems": [problem.model_dump(mode="json") for problem in problems]},
            )
        donors = await self._campaigns.donors_for_batch(campaign.batch_id)
        enrollments = [self._new_enrollment(campaign, donor.id) for donor in donors]
        transition_campaign(campaign, target)
        campaign.launched_at = now
        await self._enrollments.add_many(enrollments)
        await self._commit()
        return await self._publish_detail(campaign.id)

    async def start_scheduled(self, campaign_id: UUID) -> CampaignDetail:
        """Start a scheduled campaign once its configured time is reached."""
        campaign = await self._required_locked(campaign_id)
        require_campaign_status(campaign, CampaignStatus.SCHEDULED, "start")
        now = self._clock.now()
        if campaign.start_at > now:
            raise InvalidStateTransitionError(
                "Scheduled campaign start time has not been reached",
                {"start_at": campaign.start_at.isoformat(), "now": now.isoformat()},
            )
        transition_campaign(campaign, CampaignStatus.RUNNING)
        await self._commit()
        return await self._publish_detail(campaign.id)

    async def pause(self, campaign_id: UUID) -> CampaignDetail:
        """Pause a running campaign."""
        return await self._transition(campaign_id, CampaignStatus.PAUSED)

    async def resume(self, campaign_id: UUID) -> CampaignDetail:
        """Resume a paused campaign."""
        return await self._transition(campaign_id, CampaignStatus.RUNNING)

    async def complete(self, campaign_id: UUID) -> CampaignDetail:
        """Complete a running campaign for the future scheduler."""
        campaign = await self._required_locked(campaign_id)
        transition_campaign(campaign, CampaignStatus.COMPLETED)
        campaign.completed_at = self._clock.now()
        await self._commit()
        return await self._publish_detail(campaign.id)

    async def _transition(self, campaign_id: UUID, target: CampaignStatus) -> CampaignDetail:
        campaign = await self._required_locked(campaign_id)
        transition_campaign(campaign, target)
        await self._commit()
        return await self._publish_detail(campaign.id)

    async def _publish_detail(self, campaign_id: UUID) -> CampaignDetail:
        detail = await self._detail(campaign_id)
        # Finish the read transaction as well before calling the external publisher.
        await self._commit()
        await self._publisher.publish(
            EventType.CAMPAIGN_UPDATED.value,
            {
                "id": str(detail.id),
                "status": detail.status.value,
                "counts": {key.value: value for key, value in detail.enrollment_counts.items()},
            },
        )
        return detail

    async def _required_locked(self, campaign_id: UUID) -> Campaign:
        campaign = await self._campaigns.get_full_for_update(campaign_id)
        if campaign is None:
            raise NotFoundError("Campaign not found")
        return campaign

    async def _require_references(
        self,
        batch_id: UUID,
        primary_series_id: UUID,
        secondary_series_id: UUID,
    ) -> None:
        if await self._campaigns.get_batch(batch_id) is None:
            raise NotFoundError("Donor batch not found")
        if await self._campaigns.get_series(primary_series_id) is None:
            raise NotFoundError("Primary content series not found")
        if await self._campaigns.get_series(secondary_series_id) is None:
            raise NotFoundError("Secondary content series not found")

    async def _detail(self, campaign_id: UUID) -> CampaignDetail:
        record = await self._campaigns.get_summary(campaign_id)
        if record is None:
            raise RuntimeError("Persisted campaign could not be reloaded")
        counts = await self._enrollments.counts_by_status(campaign_id)
        return campaign_detail(record, counts)

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _new_enrollment(campaign: Campaign, donor_id: UUID) -> Enrollment:
        return Enrollment(
            campaign_id=campaign.id,
            donor_id=donor_id,
            status=EnrollmentStatus.PENDING,
            current_series_kind=SeriesKind.PRIMARY,
            current_step_order=None,
            next_action_at=campaign.start_at,
        )
