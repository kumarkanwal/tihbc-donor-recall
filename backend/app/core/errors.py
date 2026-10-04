"""Domain exceptions and consistent HTTP error responses."""

from collections.abc import Mapping

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class DomainError(Exception):
    """Base exception for expected business failures."""

    code = "INTERNAL_ERROR"
    status_code = 500
    default_message = "An internal error occurred"

    def __init__(
        self,
        message: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = dict(details or {})
        super().__init__(self.message)


class ValidationError(DomainError):
    """Input failed domain validation."""

    code = "VALIDATION_ERROR"
    status_code = 422
    default_message = "Validation failed"


class UnauthorizedError(DomainError):
    """Authentication is required or invalid."""

    code = "UNAUTHORIZED"
    status_code = 401
    default_message = "Authentication required"


class ForbiddenError(DomainError):
    """The authenticated user lacks permission."""

    code = "FORBIDDEN"
    status_code = 403
    default_message = "Permission denied"


class NotFoundError(DomainError):
    """A requested resource does not exist."""

    code = "NOT_FOUND"
    status_code = 404
    default_message = "Resource not found"


class ConflictError(DomainError):
    """The request conflicts with existing state."""

    code = "CONFLICT"
    status_code = 409
    default_message = "Resource conflict"


class InvalidStateTransitionError(DomainError):
    """A requested state transition is not allowed."""

    code = "INVALID_STATE_TRANSITION"
    status_code = 409
    default_message = "Invalid state transition"


class UploadInvalidError(DomainError):
    """An uploaded file is invalid."""

    code = "UPLOAD_INVALID"
    status_code = 400
    default_message = "Upload is invalid"


class PreviewExpiredError(DomainError):
    """A batch preview token has expired."""

    code = "PREVIEW_EXPIRED"
    status_code = 410
    default_message = "Preview has expired"


class SlotFullError(DomainError):
    """An appointment slot has no remaining capacity."""

    code = "SLOT_FULL"
    status_code = 409
    default_message = "Appointment slot is full"


class InternalError(DomainError):
    """A safe internal failure for service-level use."""


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: object,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": jsonable_encoder(details),
            }
        },
    )


def _safe_request_validation_errors(exc: RequestValidationError) -> list[dict[str, object]]:
    """Return actionable validation metadata without echoing request values."""
    return [{key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()]


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map a domain error to its documented HTTP response."""
    del request
    if not isinstance(exc, DomainError):
        raise TypeError("Expected DomainError")
    return _error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def request_validation_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Map framework validation failures to the shared error shape."""
    del request
    if not isinstance(exc, RequestValidationError):
        raise TypeError("Expected RequestValidationError")
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": _safe_request_validation_errors(exc)},
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures and return a safe shared error response."""
    logger.exception(
        "unhandled_exception",
        request_id=getattr(request.state, "request_id", None),
        path=request.url.path,
        error_type=type(exc).__name__,
    )
    return _error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred",
        details={},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception-to-response mappings."""
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
