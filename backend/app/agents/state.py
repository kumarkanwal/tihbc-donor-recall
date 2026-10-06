"""Typed LangGraph state and public agent result models."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, TypedDict
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import DeclineReason, ResponseIntent

DetectedLanguage = Literal["en", "ur", "roman_ur"]
AwaitingContext = Literal["none", "slot_choice", "decline_reason"]


class OfferedSlot(BaseModel):
    """Safe appointment context exposed to the agent."""

    id: UUID
    starts_at: datetime
    center_name: str
    label: str


class AgentResult(BaseModel):
    """Structured, database-independent reply classification."""

    intent: ResponseIntent
    confidence: float = Field(ge=0, le=1)
    detected_language: DetectedLanguage
    requested_date: date | None = None
    selected_slot_id: UUID | None = None
    decline_reason: DeclineReason | None = None
    trace_id: str | None = None


class ReplyState(TypedDict, total=False):
    """State carried through the deterministic reply graph."""

    text: str
    donor_language: Literal["en", "ur"]
    awaiting: AwaitingContext
    offered_slots: list[OfferedSlot]
    today: date
    confidence_threshold: float
    detected_language: DetectedLanguage
    intent: ResponseIntent
    confidence: float
    requested_date: date | None
    selected_slot_id: UUID | None
    decline_reason: DeclineReason | None
    result: AgentResult


@dataclass(frozen=True)
class AgentMetadata:
    """Non-personal identifiers and context attached to one trace."""

    campaign_id: UUID
    enrollment_id: UUID
    donor_language: Literal["en", "ur"]
    awaiting: AwaitingContext
    environment: str


@dataclass(frozen=True)
class AgentExecution:
    """Agent result plus provider diagnostics used by evaluation."""

    result: AgentResult
    provider: str | None
    model: str | None
    fallback_count: int
