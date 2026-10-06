"""Structured JSON logging and request correlation middleware."""

import logging
import re
from collections.abc import Mapping
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from structlog.typing import EventDict, WrappedLogger

REQUEST_ID_HEADER = "X-Request-ID"
PHONE_PATTERN = re.compile(r"(\+923\d{2})\d{5}(\d{2})")
SECRET_PATTERN = re.compile(
    r"(?i)(\b(?:api_key|key|token)\s*[=:]\s*)([^&\s,;\"']+)"
    r"|(\bauthorization\s*[=:]\s*)(?:bearer\s+)?([^&\s,;\"']+)"
)
SECRET_KEYS = {"authorization", "api_key", "key", "token"}
REDACTED = "***"


def _mask_value(value: object) -> object:
    if isinstance(value, str):
        return PHONE_PATTERN.sub(r"\1*****\2", value)
    if isinstance(value, Mapping):
        return {key: _mask_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_mask_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_mask_value(item) for item in value)
    return value


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return SECRET_PATTERN.sub(_replace_secret, value)
    if isinstance(value, Mapping):
        return {
            key: REDACTED if str(key).lower() in SECRET_KEYS else _redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    return value


def _replace_secret(match: re.Match[str]) -> str:
    prefix = match.group(1) or match.group(3)
    return f"{prefix}{REDACTED}"


def mask_phone_numbers(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Mask Pakistani mobile numbers throughout a structured log event."""
    del logger, method_name
    return {key: _mask_value(value) for key, value in event_dict.items()}


def redact_secrets(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Redact credentials in structured fields and rendered URL-like strings."""
    del logger, method_name
    return {
        key: REDACTED if str(key).lower() in SECRET_KEYS else _redact_value(value)
        for key, value in event_dict.items()
    }


def mask_email_address(email: str) -> str:
    """Mask the local part of an email address for safe authentication logs."""
    local_part, separator, domain = email.partition("@")
    if not separator:
        return "***"
    visible_prefix = local_part[:1]
    return f"{visible_prefix}***@{domain}"


def mask_phone_number(phone: str) -> str:
    """Mask one Pakistani mobile number for safe display or logging."""
    return PHONE_PATTERN.sub(r"\1*****\2", phone)


def configure_logging(log_level: str) -> None:
    """Configure standard logging and structlog to emit JSON."""
    logging.basicConfig(format="%(message)s", level=log_level, force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            mask_phone_numbers,
            redact_secrets,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[log_level]
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Bind a caller-provided or generated request ID to logs and responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
