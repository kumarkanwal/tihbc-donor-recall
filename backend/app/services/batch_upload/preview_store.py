"""Redis-backed temporary donor batch previews."""

import secrets
from datetime import datetime, timedelta
from typing import Protocol

from pydantic import ValidationError as PydanticValidationError

from app.core.clock import Clock
from app.core.errors import PreviewExpiredError
from app.schemas.donor_batch import StoredBatchPreview

PREVIEW_KEY_PREFIX = "batch_preview:"


class PreviewCache(Protocol):
    """Redis operations required by preview storage."""

    async def set(self, name: str, value: str, *, ex: int) -> object:
        """Store one expiring string value."""

    async def get(self, name: str) -> str | bytes | None:
        """Return one stored string value."""

    async def delete(self, *names: str) -> int:
        """Delete one or more values."""


class PreviewStore:
    """Store complete previews with real and demo-clock expiry."""

    def __init__(self, cache: PreviewCache, current_clock: Clock, ttl_minutes: int) -> None:
        self._cache = cache
        self._clock = current_clock
        self._ttl_seconds = ttl_minutes * 60

    def expires_at(self) -> datetime:
        """Return the demo-clock expiry for a newly created preview."""
        return self._clock.now() + timedelta(seconds=self._ttl_seconds)

    async def save(self, preview: StoredBatchPreview) -> str:
        """Store a preview under a cryptographically random token."""
        token = secrets.token_urlsafe(32)
        await self._cache.set(
            self._key(token),
            preview.model_dump_json(),
            ex=self._ttl_seconds,
        )
        return token

    async def get(self, token: str) -> StoredBatchPreview:
        """Return a live preview or raise the documented expiry error."""
        payload = await self._cache.get(self._key(token))
        if payload is None:
            raise PreviewExpiredError()
        try:
            preview = StoredBatchPreview.model_validate_json(payload)
        except (PydanticValidationError, UnicodeDecodeError):
            await self.delete(token)
            raise PreviewExpiredError() from None
        if preview.expires_at <= self._clock.now():
            await self.delete(token)
            raise PreviewExpiredError()
        return preview

    async def delete(self, token: str) -> None:
        """Delete a consumed or invalid preview."""
        await self._cache.delete(self._key(token))

    @staticmethod
    def _key(token: str) -> str:
        return f"{PREVIEW_KEY_PREFIX}{token}"
