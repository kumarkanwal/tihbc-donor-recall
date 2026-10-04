"""Tests for deterministic OpenAPI export."""

import json
from pathlib import Path

from app.export_openapi import build_openapi_json, export_openapi


def test_build_openapi_json_is_sorted_and_stable() -> None:
    first = build_openapi_json()
    second = build_openapi_json()
    schema = json.loads(first)

    assert first == second
    assert first.endswith("\n")
    assert list(schema) == sorted(schema)
    assert "/api/v1/content-series" in schema["paths"]
    assert "/api/v1/media" in schema["paths"]


def test_export_openapi_writes_repeatable_utf8_output(tmp_path: Path) -> None:
    output_path = tmp_path / "frontend" / "openapi.json"

    export_openapi(output_path)
    first = output_path.read_bytes()
    export_openapi(output_path)

    assert output_path.read_bytes() == first
    assert first == build_openapi_json().encode()
