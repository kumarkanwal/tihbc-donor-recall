"""Staff-accessible donor simulator routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import require_role
from app.api.simulator_deps import (
    get_simulator_query_service,
    get_simulator_receipt_service,
    get_simulator_reply_service,
)
from app.models.enums import UserRole
from app.schemas.simulator import (
    ConversationPage,
    MessagePage,
    OpenConversationResult,
    SimulatorMessage,
    SimulatorReply,
)
from app.schemas.user import UserOut
from app.services.simulator.query import SimulatorQueryService
from app.services.simulator.receipts import SimulatorReceiptService
from app.services.simulator.replies import SimulatorReplyService

router = APIRouter(prefix="/simulator/conversations", tags=["Simulator"])
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


@router.get("", response_model=ConversationPage, summary="List simulator conversations")
async def conversations(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[SimulatorQueryService, Depends(get_simulator_query_service)],
    campaign_id: UUID | None = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConversationPage:
    """Return masked donor-picker previews and unread counts."""
    del current_user
    return await service.conversations(
        campaign_id=campaign_id, search=search, page=page, page_size=page_size
    )


@router.get("/{donor_id}/messages", response_model=MessagePage, summary="List simulator messages")
async def messages(
    donor_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[SimulatorQueryService, Depends(get_simulator_query_service)],
    before: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> MessagePage:
    """Return a stable chronological slice, with a cursor to older messages."""
    del current_user
    return await service.messages(donor_id, before=before, limit=limit)


@router.post(
    "/{donor_id}/actions/open",
    response_model=OpenConversationResult,
    summary="Open simulator conversation",
)
async def open_conversation(
    donor_id: UUID,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[SimulatorReceiptService, Depends(get_simulator_receipt_service)],
) -> OpenConversationResult:
    """Mark delivered outreach read if the donor supports read receipts."""
    del current_user
    return await service.open(donor_id)


@router.post(
    "/{donor_id}/replies",
    response_model=SimulatorMessage,
    status_code=status.HTTP_201_CREATED,
    summary="Store simulator donor reply",
)
async def reply(
    donor_id: UUID,
    request: SimulatorReply,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[SimulatorReplyService, Depends(get_simulator_reply_service)],
) -> SimulatorMessage:
    """Store an inbound message and suspend further steps without classifying intent."""
    del current_user
    return await service.reply(donor_id, request)
