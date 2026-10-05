"""Built-in simulator messaging provider."""

from uuid import UUID

import structlog

from app.messaging.base import MessagingProvider, OutboundButton, ProviderSendResult
from app.models.enums import MediaType, MessageStatus

logger = structlog.get_logger(__name__)


class SimulatorProvider(MessagingProvider):
    """Accept messages into the database-backed simulator transport."""

    async def send_template_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
        media_type: MediaType,
        media_url: str | None,
    ) -> ProviderSendResult:
        del recipient, body, media_type, media_url
        return self._accepted(message_id, "template")

    async def send_text_message(
        self,
        *,
        message_id: UUID,
        recipient: str,
        body: str,
    ) -> ProviderSendResult:
        del recipient, body
        return self._accepted(message_id, "text")

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
        del recipient, body, buttons, media_type, media_url
        return self._accepted(message_id, "interactive")

    async def report_status_update(
        self,
        *,
        provider_message_id: str,
        status: MessageStatus,
    ) -> None:
        logger.info(
            "simulator_message_status_reported",
            provider_message_id=provider_message_id,
            status=status.value,
        )

    @staticmethod
    def _accepted(message_id: UUID, kind: str) -> ProviderSendResult:
        provider_message_id = f"sim-{message_id}"
        logger.info(
            "simulator_message_accepted",
            message_id=str(message_id),
            kind=kind,
        )
        return ProviderSendResult(provider_message_id=provider_message_id)
