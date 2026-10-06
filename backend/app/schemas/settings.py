"""Settings integration response schemas."""

from pydantic import BaseModel

from app.models.enums import MessageCategory


class IntegrationTemplateOut(BaseModel):
    """One mocked provider template sourced from an active series step."""

    name: str
    status: str
    category: MessageCategory


class IntegrationSettingsOut(BaseModel):
    """Mocked WhatsApp integration status for the demo settings screen."""

    business_verified: bool
    phone_number: str
    display_name: str
    quality_rating: str
    messaging_limit: int
    templates: list[IntegrationTemplateOut]
