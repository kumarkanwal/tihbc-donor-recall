"""Public simulator conversation and message queries."""

from uuid import UUID

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import mask_phone_number
from app.repositories.donor import DonorRepository
from app.repositories.simulator_conversations import ConversationRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.schemas.simulator import (
    ConversationPage,
    MessagePage,
    SimulatorConversation,
    SimulatorDonor,
    SimulatorMessage,
)
from app.services.messaging.payloads import message_created_payload


class SimulatorQueryService:
    """Read masked donor-picker data and stable chronological message slices."""

    def __init__(
        self,
        donors: DonorRepository,
        conversations: ConversationRepository,
        messages: SimulatorMessageRepository,
    ) -> None:
        self._donors = donors
        self._conversations = conversations
        self._messages = messages

    async def conversations(
        self,
        *,
        campaign_id: UUID | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> ConversationPage:
        """Return paginated thread previews with masked phones."""
        rows, total = await self._conversations.list_threads(
            campaign_id=campaign_id,
            search=search,
            page=page,
            page_size=page_size,
        )
        items = [
            SimulatorConversation(
                donor=SimulatorDonor(
                    id=row.donor.id,
                    name=row.donor.full_name,
                    phone=mask_phone_number(row.donor.phone_e164),
                    language=row.donor.language,
                    sim_reachable=row.donor.sim_reachable,
                    read_receipts=row.donor.sim_read_receipts,
                    campaign_id=row.campaign_id,
                    campaign_name=row.campaign_name,
                ),
                last_message=SimulatorMessage.model_validate(message_created_payload(row.message)),
                unread_count=row.unread_count,
            )
            for row in rows
        ]
        return ConversationPage(items=items, total=total, page=page, page_size=page_size)

    async def messages(
        self,
        donor_id: UUID,
        *,
        before: UUID | None,
        limit: int,
    ) -> MessagePage:
        """Return the latest visible messages, oldest first within the slice."""
        if await self._donors.get(donor_id) is None:
            raise NotFoundError("Donor not found")
        cursor = None
        if before is not None:
            anchor = await self._messages.get(before)
            if anchor is None or anchor.donor_id != donor_id:
                raise ValidationError("Cursor does not belong to this conversation")
            cursor = (anchor.effective_at, anchor.id)
        rows = await self._messages.visible_page(donor_id, before=cursor, limit=limit + 1)
        selected = rows[:limit]
        return MessagePage(
            items=[
                SimulatorMessage.model_validate(message_created_payload(row))
                for row in reversed(selected)
            ],
            next_before=selected[-1].id if len(rows) > limit else None,
            limit=limit,
        )
