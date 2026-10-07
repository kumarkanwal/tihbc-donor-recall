"""Mocked messaging-integration settings reads."""

from app.repositories.settings import IntegrationSettingsRepository
from app.schemas.settings import IntegrationSettingsOut, IntegrationTemplateOut

MOCK_PHONE_NUMBER = "+92 300 0000000"
MOCK_DISPLAY_NAME = "TIHBC"
MOCK_QUALITY_RATING = "High"
MOCK_MESSAGING_LIMIT = 1_000
MOCK_TEMPLATE_STATUS = "approved"


class IntegrationSettingsService:
    """Build the stable mocked provider status from active series steps."""

    def __init__(self, repository: IntegrationSettingsRepository) -> None:
        self._repository = repository

    async def get(self) -> IntegrationSettingsOut:
        """Return mocked integration status and active series templates."""
        records = await self._repository.list_active_templates()
        templates = [
            IntegrationTemplateOut(
                series_id=record.series_id,
                step_id=record.step_id,
                name=f"{record.series_name} - Step {record.step_order}",
                status=MOCK_TEMPLATE_STATUS,
                category=record.category,
            )
            for record in records
        ]
        return IntegrationSettingsOut(
            business_verified=True,
            phone_number=MOCK_PHONE_NUMBER,
            display_name=MOCK_DISPLAY_NAME,
            quality_rating=MOCK_QUALITY_RATING,
            messaging_limit=MOCK_MESSAGING_LIMIT,
            templates=templates,
        )
