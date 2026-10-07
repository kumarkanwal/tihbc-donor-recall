"""Provider-bound schemas remain compatible with strict constrained decoding."""

import pytest
from pydantic import BaseModel

from app.agents.nodes.classify_intent import IntentOutput
from app.agents.nodes.detect_language import LanguageOutput
from app.agents.nodes.extract_details import DeclineDetails, RescheduleExpression


@pytest.mark.parametrize(
    "schema",
    [LanguageOutput, IntentOutput, RescheduleExpression, DeclineDetails],
)
def test_structured_output_schema_has_no_optional_unions(
    schema: type[BaseModel],
) -> None:
    json_schema = schema.model_json_schema()

    assert json_schema["additionalProperties"] is False
    assert set(json_schema["required"]) == set(json_schema["properties"])
    assert "anyOf" not in repr(json_schema)


def test_decline_schema_uses_explicit_none_enum_value() -> None:
    decline_reason = DeclineDetails.model_json_schema()["properties"]["decline_reason"]

    assert decline_reason["enum"] == [
        "travelling",
        "health",
        "recently_donated",
        "not_interested",
        "other",
        "none",
    ]
