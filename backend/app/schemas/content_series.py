"""Content-series request and response schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    LanguageCode,
    MediaType,
    MessageCategory,
    MessageDirection,
    MessageKind,
    MessageStatus,
    SeriesKind,
    SeriesStatus,
)
from app.schemas.donor_batch import UploadedBySummary

QuickReplyIntent = Literal["confirm", "reschedule", "decline"]


class SeriesBaseInput(BaseModel):
    """Fields shared by create and full series updates."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    kind: SeriesKind
    languages: list[LanguageCode] = Field(min_length=1)
    response_window_hours: int = Field(default=48, gt=0)
    tag_names: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_collections(self) -> "SeriesBaseInput":
        """Require unique languages and case-insensitive tag names."""
        if len(set(self.languages)) != len(self.languages):
            raise ValueError("Series languages must be unique")
        normalized_tags = [name.casefold() for name in self.tag_names]
        if any(not name or len(name) > 40 for name in self.tag_names):
            raise ValueError("Tag names must contain 1 to 40 characters")
        if len(set(normalized_tags)) != len(normalized_tags):
            raise ValueError("Tag names must be unique")
        return self


class ContentSeriesCreate(SeriesBaseInput):
    """Create one draft content series."""


class ContentSeriesUpdate(BaseModel):
    """Update selected content-series settings."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    kind: SeriesKind | None = None
    languages: list[LanguageCode] | None = Field(default=None, min_length=1)
    response_window_hours: int | None = Field(default=None, gt=0)
    tag_names: list[str] | None = None

    @model_validator(mode="after")
    def validate_collections(self) -> "ContentSeriesUpdate":
        """Validate optional collection replacements."""
        if self.languages is not None and len(set(self.languages)) != len(self.languages):
            raise ValueError("Series languages must be unique")
        if self.tag_names is None:
            return self
        normalized_tags = [name.casefold() for name in self.tag_names]
        if any(not name or len(name) > 40 for name in self.tag_names):
            raise ValueError("Tag names must contain 1 to 40 characters")
        if len(set(normalized_tags)) != len(normalized_tags):
            raise ValueError("Tag names must be unique")
        return self


class SeriesStepContentInput(BaseModel):
    """Localized body supplied for a series step."""

    language: LanguageCode
    body: str = Field(max_length=1024)


class QuickReplyButtonInput(BaseModel):
    """Localized quick-reply definition."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=40)
    intent: QuickReplyIntent
    labels: dict[LanguageCode, str]

    @model_validator(mode="after")
    def validate_labels(self) -> "QuickReplyButtonInput":
        """Enforce non-empty WhatsApp-sized labels."""
        if not self.labels:
            raise ValueError("Button labels are required")
        if any(not label or len(label) > 20 for label in self.labels.values()):
            raise ValueError("Button labels must contain 1 to 20 characters")
        return self


class SeriesStepInput(BaseModel):
    """Create one ordered content-series step."""

    delay_days: int = Field(ge=0)
    category: MessageCategory
    media_type: MediaType = MediaType.NONE
    media_url: str | None = Field(default=None, max_length=500)
    contents: list[SeriesStepContentInput] = Field(default_factory=list)
    buttons: list[QuickReplyButtonInput] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_unique_values(self) -> "SeriesStepInput":
        """Require unique localized contents and button identifiers."""
        languages = [content.language for content in self.contents]
        if len(set(languages)) != len(languages):
            raise ValueError("Step content languages must be unique")
        button_ids = [button.id.casefold() for button in self.buttons]
        if len(set(button_ids)) != len(button_ids):
            raise ValueError("Button ids must be unique")
        return self


class SeriesStepUpdate(BaseModel):
    """Replace selected fields on one series step."""

    delay_days: int | None = Field(default=None, ge=0)
    category: MessageCategory | None = None
    media_type: MediaType | None = None
    media_url: str | None = Field(default=None, max_length=500)
    contents: list[SeriesStepContentInput] | None = None
    buttons: list[QuickReplyButtonInput] | None = Field(default=None, max_length=3)

    @model_validator(mode="after")
    def validate_unique_values(self) -> "SeriesStepUpdate":
        """Require unique replacement contents and buttons."""
        if self.contents is not None:
            languages = [content.language for content in self.contents]
            if len(set(languages)) != len(languages):
                raise ValueError("Step content languages must be unique")
        if self.buttons is not None:
            button_ids = [button.id.casefold() for button in self.buttons]
            if len(set(button_ids)) != len(button_ids):
                raise ValueError("Button ids must be unique")
        return self


class SeriesReorderInput(BaseModel):
    """Complete desired ordering for one series."""

    step_ids: list[UUID] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "SeriesReorderInput":
        """Reject repeated step identifiers."""
        if len(set(self.step_ids)) != len(self.step_ids):
            raise ValueError("Step ids must be unique")
        return self


class SeriesPreviewInput(BaseModel):
    """Select a step, language, and optional real donor."""

    step_id: UUID
    language: LanguageCode
    donor_id: UUID | None = None


class ActivationProblem(BaseModel):
    """One actionable series activation problem."""

    step: int | None
    language: LanguageCode | None
    field: str
    reason: str


class SeriesStepContentOut(BaseModel):
    """Stored localized step body."""

    id: UUID
    language: LanguageCode
    body: str


class QuickReplyButtonOut(BaseModel):
    """Stored multilingual quick-reply definition."""

    id: str
    intent: QuickReplyIntent
    labels: dict[LanguageCode, str]


class SeriesStepOut(BaseModel):
    """One ordered series step with localized contents."""

    id: UUID
    step_order: int
    delay_days: int
    category: MessageCategory
    media_type: MediaType
    media_url: str | None
    contents: list[SeriesStepContentOut]
    buttons: list[QuickReplyButtonOut]


class ContentSeriesOut(BaseModel):
    """Content-series list representation."""

    id: UUID
    name: str
    description: str | None
    kind: SeriesKind
    status: SeriesStatus
    languages: list[LanguageCode]
    response_window_hours: int
    tags: list[str]
    step_count: int
    created_by: UploadedBySummary
    created_at: datetime
    updated_at: datetime


class ContentSeriesDetail(ContentSeriesOut):
    """Content series with its ordered steps."""

    steps: list[SeriesStepOut]


class ContentSeriesPage(BaseModel):
    """Paginated content-series summaries."""

    items: list[ContentSeriesOut]
    total: int
    page: int
    page_size: int


class PreviewButtonOut(BaseModel):
    """Quick reply localized for simulator preview."""

    id: str
    label: str


class SeriesPreviewMessage(BaseModel):
    """Non-persistent outbound message rendered for the simulator preview."""

    id: UUID
    donor_id: UUID | None
    direction: MessageDirection
    kind: MessageKind
    body: str
    media_type: MediaType
    media_url: str | None
    buttons: list[PreviewButtonOut]
    button_id: None = None
    reply_to_message_id: None = None
    status: MessageStatus
    created_at: datetime
    sent_at: None = None
    delivered_at: None = None
    read_at: None = None
