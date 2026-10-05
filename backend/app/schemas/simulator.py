"""Public simulator queries and discriminated donor replies."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import LanguageCode
from app.ws.events import MessagePayload


class SimulatorMessage(MessagePayload):
    """The same public message shape used by realtime events."""


class SimulatorDonor(BaseModel):
    """Masked donor-picker row with its latest matching campaign."""

    id: UUID
    name: str
    phone: str
    language: LanguageCode
    sim_reachable: bool
    read_receipts: bool
    campaign_id: UUID | None
    campaign_name: str | None


class SimulatorConversation(BaseModel):
    """Donor thread preview."""

    donor: SimulatorDonor
    last_message: SimulatorMessage
    unread_count: int


class ConversationPage(BaseModel):
    """Paginated donor threads."""

    items: list[SimulatorConversation]
    total: int
    page: int
    page_size: int


class MessagePage(BaseModel):
    """Latest message slice in chronological order, with an older-page cursor."""

    items: list[SimulatorMessage]
    next_before: UUID | None
    limit: int


class OpenConversationResult(BaseModel):
    """Number of delivered outbound messages marked read."""

    read_count: int


class TextReply(BaseModel):
    """Unclassified donor free-text reply."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=4096)


class ButtonReply(BaseModel):
    """Reply to one of a particular outbound message's localized buttons."""

    model_config = ConfigDict(extra="forbid")
    type: Literal["button"]
    button_id: str = Field(min_length=1, max_length=40)
    reply_to_message_id: UUID


SimulatorReply = Annotated[TextReply | ButtonReply, Field(discriminator="type")]
