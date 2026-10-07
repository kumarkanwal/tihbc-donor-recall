"""Provider failure classification and safe diagnostic rendering."""

import json
from collections.abc import Mapping

import httpx
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.agents.state import ProviderAttemptStatus
from app.core.logging import sanitize_log_value

MAX_ERROR_DETAIL_CHARACTERS = 2000
OUTPUT_PARSE_FAILED = "output_parse_failed"


def provider_attempt_status(
    error: Exception,
    status: int | None,
    error_code: str | None = None,
) -> ProviderAttemptStatus:
    """Map an exception to the stable evaluation status vocabulary."""
    if error_code == OUTPUT_PARSE_FAILED:
        return "invalid_output"
    if status == 400:
        return "client_error"
    if status in {401, 403}:
        return "credentials_unavailable"
    if status == 402:
        return "payment_required"
    if status == 429:
        return "rate_limited"
    if status is not None and status >= 500:
        return "server_error"
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return "timeout"
    if isinstance(error, (ConnectionError, httpx.NetworkError)):
        return "connection_error"
    if isinstance(error, (OutputParserException, ValidationError, ValueError)):
        return "invalid_output"
    return "unknown_error"


def provider_error_code(error: Exception) -> str | None:
    """Read a stable provider code from common nested error-body shapes."""
    body = getattr(error, "body", None)
    response = getattr(error, "response", None)
    if body is None and response is not None:
        try:
            body = response.json()
        except (AttributeError, ValueError):
            return None
    if not isinstance(body, Mapping):
        return None
    nested = body.get("error")
    for candidate in (body, nested):
        if not isinstance(candidate, Mapping):
            continue
        code = candidate.get("code")
        if isinstance(code, str):
            return code
    return None


def provider_status_code(error: Exception) -> int | None:
    """Read an HTTP status from common provider exception shapes."""
    for attribute in ("status_code", "code"):
        status = getattr(error, attribute, None)
        if isinstance(status, int):
            return status
    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)
    return response_status if isinstance(response_status, int) else None


def safe_provider_error_detail(error: Exception, api_key: str) -> str:
    """Render a bounded provider error after masking personal data and secrets."""
    body = getattr(error, "body", None)
    response = getattr(error, "response", None)
    if body is None and response is not None:
        try:
            body = response.json()
        except (AttributeError, ValueError):
            body = getattr(response, "text", None)
    if body is None:
        body = str(error)
    rendered = json.dumps(sanitize_log_value(body), ensure_ascii=False, default=str)
    return rendered.replace(api_key, "***")[:MAX_ERROR_DETAIL_CHARACTERS]
