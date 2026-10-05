"""Provider-neutral outbound messaging contract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.models.enums import MediaType, MessageStatus


@dataclass(frozen=True)
class OutboundButton:
    """One localized interactive-message button."""

    id: str
    label: str


@dataclass(frozen=True)
class ProviderSendResult:
    """Provider identifier assigned to an accepted message."""

    provider_message_id: str


class MessagingProvider(ABC):
    """Send messages without exposing a concrete transport to business logic."""

    @abstractmethod
    async def send_template_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        """Send one rendered template message."""

    @abstractmethod
    async def send_text_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
    ) -> ProviderSendResult:
        """Send one free-form text message."""

    @abstractmethod
    async def send_interactive_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        buttons: tuple[OutboundButton, ...],
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        """Send one rendered message with localized quick replies."""

    @abstractmethod
    async def report_status_update(
        self,
        *,
        provider_message_id: str,
        status: MessageStatus,
    ) -> None:
        """Acknowledge a provider delivery-status transition."""
