"""Read campaigns and enrollments."""

from uuid import UUID

from app.core.errors import NotFoundError
from app.models.enums import CampaignStatus, EnrollmentStatus
from app.repositories.campaign import CampaignRepository
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.campaign import (
    CampaignDetail,
    CampaignPage,
    EnrollmentDetail,
    EnrollmentPage,
)
from app.services.campaigns.mappers import (
    campaign_detail,
    campaign_out,
    enrollment_detail,
    enrollment_out,
)


class CampaignQueryService:
    """Build API views of campaigns and their enrollments."""

    def __init__(
        self,
        campaign_repository: CampaignRepository,
        enrollment_repository: EnrollmentRepository,
    ) -> None:
        self._campaigns = campaign_repository
        self._enrollments = enrollment_repository

    async def list_campaigns(
        self,
        *,
        status: CampaignStatus | None,
        page: int,
        page_size: int,
    ) -> CampaignPage:
        """Return a filtered campaign page."""
        result = await self._campaigns.list_filtered(
            status=status,
            page=page,
            page_size=page_size,
        )
        return CampaignPage(
            items=[campaign_out(record) for record in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def get_campaign(self, campaign_id: UUID) -> CampaignDetail:
        """Return one campaign and all enrollment-status counts."""
        record = await self._campaigns.get_summary(campaign_id)
        if record is None:
            raise NotFoundError("Campaign not found")
        counts = await self._enrollments.counts_by_status(campaign_id)
        return campaign_detail(record, counts)

    async def list_enrollments(
        self,
        campaign_id: UUID,
        *,
        status: EnrollmentStatus | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> EnrollmentPage:
        """Return filtered campaign enrollments with masked phones."""
        if await self._campaigns.get(campaign_id) is None:
            raise NotFoundError("Campaign not found")
        result = await self._enrollments.list_for_campaign(
            campaign_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
        )
        return EnrollmentPage(
            items=[enrollment_out(record, mask_phone=True) for record in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def get_enrollment(self, enrollment_id: UUID) -> EnrollmentDetail:
        """Return full donor, timeline, and follow-up details."""
        enrollment = await self._enrollments.get_full(enrollment_id)
        if enrollment is None:
            raise NotFoundError("Enrollment not found")
        return enrollment_detail(enrollment)
