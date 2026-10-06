"""Tests for request correlation and log redaction."""

import json
import logging

import structlog
from fastapi.testclient import TestClient

from app.core.logging import (
    REQUEST_ID_HEADER,
    configure_logging,
    mask_email_address,
    mask_phone_numbers,
    redact_secrets,
)
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


def test_configured_secrets_never_appear_in_captured_logs() -> None:
    secret = "configured-provider-secret"
    with structlog.testing.capture_logs(processors=[redact_secrets]) as logs:
        structlog.get_logger().warning(
            "provider_warning",
            url=f"https://provider.test/models?key={secret}&page=1",
            api_key=secret,
            Authorization=f"Bearer {secret}",
            nested={"token": secret},
        )

    assert secret not in json.dumps(logs)


def test_http_client_request_logging_is_suppressed() -> None:
    configure_logging("DEBUG")

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
