"""Tests for request correlation and log redaction."""

import json

from fastapi.testclient import TestClient

from app.core.logging import REQUEST_ID_HEADER, mask_email_address, mask_phone_numbers
from app.main import app


def test_request_id_is_generated_and_returned() -> None:
    response = TestClient(app).get("/health/live")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]


def test_existing_request_id_is_preserved() -> None:
    response = TestClient(app).get(
        "/health/live",
        headers={REQUEST_ID_HEADER: "caller-request-id"},
    )

    assert response.headers[REQUEST_ID_HEADER] == "caller-request-id"


def test_phone_numbers_are_masked_recursively() -> None:
    event = mask_phone_numbers(
        None,
        "info",
        {
            "event": "Contact +923001234567",
            "donor": {"phone": "+923009876567"},
        },
    )

    rendered = json.dumps(event)
    assert "+92300*****67" in rendered
    assert "+923001234567" not in rendered
    assert "+923009876567" not in rendered


def test_email_address_masks_local_part() -> None:
    assert mask_email_address("admin@tihbc.demo") == "a***@tihbc.demo"
    assert mask_email_address("not-an-email") == "***"
