"""Schema-level content-series validation tests."""

import pytest
from pydantic import ValidationError

from app.schemas.content_series import ContentSeriesCreate, SeriesStepInput


def _series(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "name": "Regular Donor Recall",
        "kind": "primary",
        "languages": ["en", "ur"],
        "response_window_hours": 48,
        "tag_names": ["regular", "recall"],
    }
    values.update(overrides)
    return values


def _step(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "delay_days": 0,
        "category": "utility",
        "media_type": "none",
        "contents": [{"language": "en", "body": "Hello"}],
        "buttons": [
            {
                "id": "btn_confirm",
                "intent": "confirm",
                "labels": {"en": "Confirm", "ur": "تصدیق کریں"},
            }
        ],
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    "overrides",
    [
        {"languages": ["en", "en"]},
        {"tag_names": ["Recall", "recall"]},
        {"tag_names": ["x" * 41]},
        {"response_window_hours": 0},
    ],
)
def test_series_collection_and_window_rules(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ContentSeriesCreate.model_validate(_series(**overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"delay_days": -1},
        {"contents": [{"language": "en", "body": "x" * 1025}]},
        {
            "buttons": [
                {"id": "same", "intent": "confirm", "labels": {"en": "Yes"}},
                {"id": "SAME", "intent": "decline", "labels": {"en": "No"}},
            ]
        },
        {
            "buttons": [
                {"id": f"b{index}", "intent": "confirm", "labels": {"en": "Yes"}}
                for index in range(4)
            ]
        },
        {"buttons": [{"id": "bad", "intent": "question", "labels": {"en": "Ask"}}]},
        {"buttons": [{"id": "long", "intent": "confirm", "labels": {"en": "x" * 21}}]},
    ],
)
def test_step_and_button_rules(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SeriesStepInput.model_validate(_step(**overrides))
