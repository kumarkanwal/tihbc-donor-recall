"""Regression checks for the documented seeded series catalog."""

from app.models.enums import MessageCategory, SeriesKind
from app.seed.content import RECALL_BUTTONS, SERIES_SEEDS
from app.services.templates.renderer import validate_template


def test_seed_series_match_documented_structure_and_valid_templates() -> None:
    assert [series.name for series in SERIES_SEEDS] == [
        "Regular Donor Recall",
        "Lapsed Donor Win-back",
        "First-Time Donor Return",
        "Final Follow-up",
    ]
    assert [series.kind for series in SERIES_SEEDS] == [
        SeriesKind.PRIMARY,
        SeriesKind.PRIMARY,
        SeriesKind.PRIMARY,
        SeriesKind.SECONDARY,
    ]
    assert [[step.delay_days for step in series.steps] for series in SERIES_SEEDS] == [
        [0, 3, 7],
        [0, 3, 7],
        [0, 4],
        [0, 3],
    ]
    assert SERIES_SEEDS[0].steps[0].category == MessageCategory.UTILITY
    assert SERIES_SEEDS[1].steps[0].category == MessageCategory.MARKETING
    for series in SERIES_SEEDS:
        for step in series.steps:
            validate_template(step.english)
            validate_template(step.urdu)
            assert len(step.english) <= 1024
            assert len(step.urdu) <= 1024


def test_every_recall_step_uses_the_exact_three_quick_replies() -> None:
    assert RECALL_BUTTONS == [
        {
            "id": "btn_confirm",
            "intent": "confirm",
            "labels": {"en": "Confirm", "ur": "تصدیق کریں"},
        },
        {
            "id": "btn_reschedule",
            "intent": "reschedule",
            "labels": {"en": "Reschedule", "ur": "دوسرا وقت"},
        },
        {
            "id": "btn_decline",
            "intent": "decline",
            "labels": {"en": "Not now", "ur": "ابھی نہیں"},
        },
    ]
