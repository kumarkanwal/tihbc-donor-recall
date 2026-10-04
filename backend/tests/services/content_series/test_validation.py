"""Tests for cross-field and activation validation."""

from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from app.models.enums import (
    LanguageCode,
    MediaType,
    MessageCategory,
    SeriesKind,
)
from app.models.series import ContentSeries, SeriesStep, SeriesStepContent
from app.schemas.content_series import QuickReplyButtonInput, SeriesStepContentInput
from app.services.content_series.validation import activation_problems, validate_step_values


def test_step_values_require_supported_content_and_all_button_labels() -> None:
    contents = [SeriesStepContentInput(language=LanguageCode.UR, body="متن")]
    button = QuickReplyButtonInput(
        id="btn_confirm",
        intent="confirm",
        labels={LanguageCode.EN: "Confirm"},
    )

    with pytest.raises(ValidationError, match="not enabled"):
        validate_step_values([LanguageCode.EN], contents, [])
    with pytest.raises(ValidationError, match="missing"):
        validate_step_values([LanguageCode.EN, LanguageCode.UR], [], [button])


def test_step_values_reject_unknown_template_variables() -> None:
    contents = [SeriesStepContentInput(language=LanguageCode.EN, body="Hello {{phone_number}}")]

    with pytest.raises(ValidationError, match="unknown variables"):
        validate_step_values([LanguageCode.EN], contents, [])


def test_activation_returns_all_missing_content_and_media_problems() -> None:
    series = ContentSeries(
        name="Incomplete",
        kind=SeriesKind.PRIMARY,
        languages=[LanguageCode.EN, LanguageCode.UR],
        created_by_id=uuid4(),
        steps=[
            SeriesStep(
                step_order=1,
                delay_days=0,
                category=MessageCategory.UTILITY,
                media_type=MediaType.IMAGE,
                media_url=None,
                buttons=[],
                contents=[SeriesStepContent(language=LanguageCode.EN, body="")],
            )
        ],
    )

    problems = activation_problems(series)

    assert {(item.step, item.language, item.field) for item in problems} == {
        (1, LanguageCode.EN, "body"),
        (1, LanguageCode.UR, "body"),
        (1, None, "media_url"),
    }


def test_activation_requires_at_least_one_step() -> None:
    series = ContentSeries(
        name="Empty",
        kind=SeriesKind.PRIMARY,
        languages=[LanguageCode.EN],
        created_by_id=uuid4(),
        steps=[],
    )

    assert activation_problems(series)[0].field == "steps"
