"""Minimal prompt sanitization for donor phone numbers."""

import re

PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?92|0)?3\d{2}[\s-]?\d{7}(?!\w)")


def sanitize_reply_text(text: str) -> str:
    """Remove Pakistani mobile numbers before tracing or model invocation."""
    return PHONE_PATTERN.sub("[phone]", text)
