"""Provider failure classification and safe diagnostic rendering."""

import json

import httpx
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from app.agents.state import ProviderAttemptStatus
from app.core.logging import sanitize_log_value

MAX_ERROR_DETAIL_CHARACTERS = 2000


def provider_attempt_status(error: Exception, status: int | None) -> ProviderAttemptStatus:
    """Map an exception to the stable evaluation status vocabulary."""
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
