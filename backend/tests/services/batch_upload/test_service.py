"""Tests for donor batch upload orchestration."""

from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import ValidationError
from app.models.donor import DonorBatch, Segment
from app.models.enums import UserRole
from app.repositories.donor import DonorRepository, SegmentRepository
from app.repositories.donor_batch import DonorBatchRepository
from app.schemas.donor_batch import BatchImportRequest
from app.schemas.user import UserOut
from app.services.batch_upload.preview_store import PreviewStore
from app.services.batch_upload.sample_file import generate_sample_csv
from app.services.batch_upload.service import BatchUploadService
from tests.services.batch_upload.test_preview_store import FakePreviewCache


def _service(
    *,
    session: AsyncSession | None = None,
    batches: DonorBatchRepository | None = None,
    donors: DonorRepository | None = None,
    segments: SegmentRepository | None = None,
    store: PreviewStore | None = None,
) -> BatchUploadService:
    resolved_session = session or cast(AsyncSession, Mock(spec=AsyncSession))
    return BatchUploadService(
        resolved_session,
        batches or cast(DonorBatchRepository, Mock(spec=DonorBatchRepository)),
        donors or cast(DonorRepository, Mock(spec=DonorRepository)),
        segments or cast(SegmentRepository, Mock(spec=SegmentRepository)),
        store or PreviewStore(FakePreviewCache(), Clock(), 30),
        Clock(),
        max_size_mb=1,
        max_rows=10,
    )


@pytest.mark.asyncio
async def test_preview_keeps_first_duplicate_and_returns_existing_phone_warning() -> None:
    segment = Segment(id=uuid4(), key="regular", label="Regular")
    segment_repository = Mock(spec=SegmentRepository)
    segment_repository.list_all = AsyncMock(return_value=(segment,))
    donor_repository = Mock(spec=DonorRepository)
    donor_repository.existing_batch_names = AsyncMock(return_value={"+923001234567": "Test Batch"})
    content = (
        b"name,phone,segment,language\n"
        b"Ali Khan,0300-1234567,Regular,English\n"
        b"Later Duplicate,+92 300 1234567,Regular,English\n"
    )

    preview = await _service(
        donors=cast(DonorRepository, donor_repository),
        segments=cast(SegmentRepository, segment_repository),
    ).preview("donors.csv", content)

    assert preview.valid_rows == 1
    assert preview.invalid_rows == 1
    assert preview.sample_valid_rows[0].row == 2
    assert preview.sample_valid_rows[0].name == "Ali Khan"
    assert preview.sample_valid_rows[0].phone == "+923001234567"
    assert preview.errors[0].row == 3
    assert preview.errors[0].reason == "Duplicate of row 2"
    assert preview.warnings[0].row == 2
    assert preview.warnings[0].phone == "+92300*****67"
    assert preview.warnings[0].existing_batch_name == "Test Batch"


@pytest.mark.asyncio
async def test_generated_sample_file_previews_with_three_valid_rows() -> None:
    segments = tuple(
        Segment(id=uuid4(), key=key, label=label)
        for key, label in (
            ("regular", "Regular"),
            ("lapsed", "Lapsed"),
            ("first_time", "First Time"),
        )
    )
    segment_repository = Mock(spec=SegmentRepository)
    segment_repository.list_all = AsyncMock(return_value=segments)
    donor_repository = Mock(spec=DonorRepository)
    donor_repository.existing_batch_names = AsyncMock(return_value={})

    preview = await _service(
        donors=cast(DonorRepository, donor_repository),
        segments=cast(SegmentRepository, segment_repository),
    ).preview("sample.csv", generate_sample_csv())

    assert preview.total_rows == 3
    assert preview.valid_rows == 3
    assert preview.errors == []


@pytest.mark.asyncio
async def test_import_rolls_back_when_donor_insert_fails() -> None:
    cache = FakePreviewCache()
    store = PreviewStore(cache, Clock(), 30)
    segment = Segment(id=uuid4(), key="regular", label="Regular")
    segment_repository = Mock(spec=SegmentRepository)
    segment_repository.list_all = AsyncMock(return_value=(segment,))
    donor_repository = Mock(spec=DonorRepository)
    donor_repository.existing_batch_names = AsyncMock(return_value={})
    donor_repository.add_many = AsyncMock(side_effect=RuntimeError("insert failed"))
    batch_repository = Mock(spec=DonorBatchRepository)

    async def add_batch(batch: DonorBatch) -> DonorBatch:
        batch.id = uuid4()
        batch.created_at = datetime(2026, 10, 3, tzinfo=UTC)
        return batch

    batch_repository.add = AsyncMock(side_effect=add_batch)
    session = Mock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    service = _service(
        session=cast(AsyncSession, session),
        batches=cast(DonorBatchRepository, batch_repository),
        donors=cast(DonorRepository, donor_repository),
        segments=cast(SegmentRepository, segment_repository),
        store=store,
    )
    preview = await service.preview(
        "donors.csv",
        b"name,phone,segment,language\nAhsan,03001234567,regular,en\n",
    )

    with pytest.raises(RuntimeError, match="insert failed"):
        await service.import_batch(
            BatchImportRequest(name="Test Batch", preview_token=preview.preview_token),
            _admin(),
        )

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
    assert await store.get(preview.preview_token)


@pytest.mark.asyncio
async def test_import_rejects_preview_without_valid_donors_before_writing() -> None:
    store = PreviewStore(FakePreviewCache(), Clock(), 30)
    segment_repository = Mock(spec=SegmentRepository)
    segment_repository.list_all = AsyncMock(return_value=())
    donor_repository = Mock(spec=DonorRepository)
    donor_repository.existing_batch_names = AsyncMock(return_value={})
    donor_repository.add_many = AsyncMock()
    batch_repository = Mock(spec=DonorBatchRepository)
    batch_repository.add = AsyncMock()
    session = Mock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    service = _service(
        session=cast(AsyncSession, session),
        batches=cast(DonorBatchRepository, batch_repository),
        donors=cast(DonorRepository, donor_repository),
        segments=cast(SegmentRepository, segment_repository),
        store=store,
    )
    preview = await service.preview(
        "invalid.csv",
        b"name,phone,segment,language\nInvalid,not-a-phone,regular,en\n",
    )

    with pytest.raises(ValidationError) as error:
        await service.import_batch(
            BatchImportRequest(name="Empty Batch", preview_token=preview.preview_token),
            _admin(),
        )

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.message == "No valid donors to import"
    batch_repository.add.assert_not_awaited()
    donor_repository.add_many.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.rollback.assert_not_awaited()
    assert await store.get(preview.preview_token)


def _admin() -> UserOut:
    return UserOut(
        id=uuid4(),
        email="admin@example.test",
        full_name="TIHBC Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
