"""Tests for Redis-backed batch preview expiry."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.clock import Clock
from app.core.errors import PreviewExpiredError
from app.schemas.donor_batch import StoredBatchPreview, StoredDonorRow
from app.services.batch_upload.preview_store import PreviewStore


class FakeClockPersistence:
    """In-memory clock persistence for expiry tests."""

    def __init__(self) -> None:
        self.offset_seconds = 0

    async def load_offset_seconds(self) -> int:
        return self.offset_seconds

    async def increment_offset_seconds(self, seconds: int) -> int:
        self.offset_seconds += seconds
        return self.offset_seconds

    async def set_offset_seconds(self, seconds: int) -> int:
        self.offset_seconds = seconds
        return self.offset_seconds


class FakePreviewCache:
    """Minimal string cache retaining values until explicitly deleted."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int] = {}

    async def set(self, name: str, value: str, *, ex: int) -> object:
        self.values[name] = value
        self.expiries[name] = ex
        return True

    async def get(self, name: str) -> str | bytes | None:
        return self.values.get(name)

    async def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            if name in self.values:
                deleted += 1
                del self.values[name]
        return deleted


@pytest.mark.asyncio
async def test_preview_expires_when_demo_clock_advances() -> None:
    test_clock = Clock()
    await test_clock.initialize(FakeClockPersistence())
    cache = FakePreviewCache()
    store = PreviewStore(cache, test_clock, ttl_minutes=30)
    preview = _preview(store)
    token = await store.save(preview)

    assert (await store.get(token)).valid_rows == 1
    assert next(iter(cache.expiries.values())) == 1800

    await test_clock.advance(timedelta(minutes=31))

    with pytest.raises(PreviewExpiredError):
        await store.get(token)
    assert cache.values == {}


@pytest.mark.asyncio
async def test_unknown_preview_token_is_expired() -> None:
    store = PreviewStore(FakePreviewCache(), Clock(), ttl_minutes=30)

    with pytest.raises(PreviewExpiredError):
        await store.get("unknown")


def _preview(store: PreviewStore) -> StoredBatchPreview:
    return StoredBatchPreview(
        original_filename="donors.csv",
        total_rows=1,
        valid_rows=1,
        invalid_rows=0,
        donors=[
            StoredDonorRow(
                row=2,
                name="Ahsan Khan",
                phone="+923001234567",
                segment="regular",
                segment_id=uuid4(),
                language="en",
            )
        ],
        segment_breakdown=[],
        language_breakdown=[],
        errors=[],
        warnings=[],
        expires_at=store.expires_at(),
    )
