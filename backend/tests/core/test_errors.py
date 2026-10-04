"""Tests for the shared API error contract."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    InternalError,
    InvalidStateTransitionError,
    NotFoundError,
    PreviewExpiredError,
    SlotFullError,
    UnauthorizedError,
    UploadInvalidError,
    ValidationError,
    register_exception_handlers,
)

ERROR_CASES = (
    (ValidationError, "VALIDATION_ERROR", 422),
    (UnauthorizedError, "UNAUTHORIZED", 401),
    (ForbiddenError, "FORBIDDEN", 403),
    (NotFoundError, "NOT_FOUND", 404),
    (ConflictError, "CONFLICT", 409),
    (InvalidStateTransitionError, "INVALID_STATE_TRANSITION", 409),
    (UploadInvalidError, "UPLOAD_INVALID", 400),
    (PreviewExpiredError, "PREVIEW_EXPIRED", 410),
    (SlotFullError, "SLOT_FULL", 409),
    (InternalError, "INTERNAL_ERROR", 500),
)


def _client_for_exception(error: Exception) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/fail")
    async def fail() -> None:
        raise error

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(("error_type", "code", "status_code"), ERROR_CASES)
def test_domain_error_shape(
    error_type: type[DomainError],
    code: str,
    status_code: int,
) -> None:
    client = _client_for_exception(error_type("Specific failure", {"field": "value"}))

    response = client.get("/fail")

    assert response.status_code == status_code
    assert response.json() == {
        "error": {
            "code": code,
            "message": "Specific failure",
            "details": {"field": "value"},
        }
    }


def test_request_validation_uses_shared_shape() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/items/{item_id}")
    async def item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    response = TestClient(app).get("/items/not-an-integer")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["errors"]


def test_request_validation_does_not_echo_input_values() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    class DonorInput(BaseModel):
        phone: str = Field(pattern=r"^\+923\d{9}$")

    @app.post("/donors")
    async def create_donor(donor: DonorInput) -> DonorInput:
        return donor

    sensitive_phone = "+923001234567-extra"
    response = TestClient(app).post("/donors", json={"phone": sensitive_phone})

    assert response.status_code == 422
    errors = response.json()["error"]["details"]["errors"]
    assert errors
    assert all(set(error) == {"loc", "msg", "type"} for error in errors)
    assert sensitive_phone not in response.text


def test_unexpected_error_uses_safe_shared_shape() -> None:
    response = _client_for_exception(RuntimeError("sensitive detail")).get("/fail")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": {},
        }
    }
