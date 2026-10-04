"""Read campaigns and enrollments."""

from uuid import UUID

from app.core.errors import NotFoundError
from app.models.enums import CampaignStatus, EnrollmentStatus
from app.repositories.campaign import CampaignRepository
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

    def __init__(self, repository: CampaignRepository) -> None:
        self._repository = repository

    async def list_campaigns(
        self,
        *,
        status: CampaignStatus | None,
        page: int,
        page_size: int,
    ) -> CampaignPage:
        """Return a filtered campaign page."""
        result = await self._repository.list_filtered(
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
        record = await self._repository.get_summary(campaign_id)
        if record is None:
            raise NotFoundError("Campaign not found")
        counts = await self._repository.enrollment_counts(campaign_id)
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
        if await self._repository.get(campaign_id) is None:
            raise NotFoundError("Campaign not found")
        result = await self._repository.list_enrollments(
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
        enrollment = await self._repository.get_enrollment_full(enrollment_id)
        if enrollment is None:
            raise NotFoundError("Enrollment not found")
        return enrollment_detail(enrollment)
