"""PostgreSQL coverage for donor batch import and HTTP listing."""

from collections.abc import AsyncIterator
from datetime import date
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_batch_upload_service, get_current_user
from app.core.clock import Clock
from app.core.db import get_db
from app.main import app
from app.models.campaign import Campaign
from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import LanguageCode, UserRole
from app.models.user import User
from app.repositories.donor import DonorRepository, SegmentRepository
from app.repositories.donor_batch import DonorBatchRepository
from app.schemas.donor_batch import BatchImportRequest, StoredBatchPreview, StoredDonorRow
from app.schemas.user import UserOut
from app.services.batch_upload.preview_store import PreviewStore
from app.services.batch_upload.query_service import DonorBatchQueryService
from app.services.batch_upload.service import BatchUploadService
from tests.services.batch_upload.test_preview_store import FakePreviewCache

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_http_list_includes_imported_batch_without_campaigns(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    batch_name = f"No Campaign Batch {uuid4().hex}"
    async with postgres_session_factory() as session:
        user = await _add_user(session)
        segment = await _segment(session, "regular")
        store = PreviewStore(FakePreviewCache(), Clock(), 30)
        token = await store.save(_campaign_free_preview(store, segment))
        current_user = UserOut.model_validate(user)
        upload_service = _upload_service(session, store)

        async def override_db() -> AsyncIterator[AsyncSession]:
            yield session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: current_user
        app.dependency_overrides[get_batch_upload_service] = lambda: upload_service
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                imported = await client.post(
                    "/api/v1/donor-batches",
                    json={"name": batch_name, "preview_token": token},
                )
                assert imported.status_code == 201
                batch_id = UUID(imported.json()["id"])
                listed = await client.get("/api/v1/donor-batches", params={"search": batch_name})
                detail = await client.get(f"/api/v1/donor-batches/{batch_id}")
                donors = await client.get(f"/api/v1/donor-batches/{batch_id}/donors")
        finally:
            app.dependency_overrides.clear()

        campaign_count = await session.scalar(
            select(func.count()).select_from(Campaign).where(Campaign.batch_id == batch_id)
        )

    assert listed.status_code == 200
    listed_items = {item["id"]: item for item in listed.json()["items"]}
    assert str(batch_id) in listed_items
    assert listed_items[str(batch_id)]["campaign_count"] == 0
    assert detail.status_code == 200
    assert detail.json()["campaign_count"] == 0
    assert donors.status_code == 200
    assert donors.json()["total"] == 3
    assert campaign_count == 0


@pytest.mark.asyncio
async def test_import_and_listing_with_existing_phone_warning(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    unique_suffix = uuid4().hex
    existing_batch_name = f"Earlier Recall {unique_suffix}"
    imported_batch_name = f"October Recall {unique_suffix}"
    phone_suffix = int(unique_suffix[:8], 16) % 10_000_000
    existing_phone = f"+92300{phone_suffix:07d}"
    imported_phone = f"+92301{phone_suffix:07d}"
    async with postgres_session_factory() as session:
        user = await _add_user(session)
        segment = await _segment(session, "regular")
        await _add_existing_donor(
            session,
            user,
            segment,
            batch_name=existing_batch_name,
            phone=existing_phone,
        )
        store = PreviewStore(FakePreviewCache(), Clock(), 30)
        upload_service = _upload_service(session, store)

        preview = await upload_service.preview(
            "october.csv",
            (
                "name,phone,segment,language,city,blood_group,last_donation_date\n"
                f"Ahsan Khan,{existing_phone},Regular,English,Karachi,O+,2026-01-15\n"
                f"Fatima Ahmed,{imported_phone},regular,Urdu,Lahore,A+,15/12/2025\n"
            ).encode(),
        )
        imported = await upload_service.import_batch(
            BatchImportRequest(name=imported_batch_name, preview_token=preview.preview_token),
            UserOut.model_validate(user),
        )

        query_service = DonorBatchQueryService(
            DonorBatchRepository(session), DonorRepository(session)
        )
        batches = await query_service.list_batches(
            search=imported_batch_name, sort="-created_at", page=1, page_size=20
        )
        detail = await query_service.get_batch(imported.id)
        donors = await query_service.list_donors(
            imported.id,
            segment="regular",
            language=LanguageCode.EN,
            search="Ahsan",
            sort="full_name",
            page=1,
            page_size=20,
        )
        persisted = await session.scalar(select(Donor).where(Donor.batch_id == imported.id))

    assert preview.warnings[0].phone.startswith("+923")
    assert "*****" in preview.warnings[0].phone
    assert preview.warnings[0].existing_batch_name == existing_batch_name
    assert imported.id in {item.id for item in batches.items}
    assert detail.segment_breakdown[0].count == 2
    assert {item.language for item in detail.language_breakdown} == {
        LanguageCode.EN,
        LanguageCode.UR,
    }
    assert donors.total == 1
    assert donors.items[0].phone_e164 == f"{existing_phone[:6]}*****{existing_phone[-2:]}"
    assert persisted is not None
    assert persisted.sim_reachable is True
    assert persisted.sim_read_receipts is True


@pytest.mark.asyncio
async def test_import_rolls_back_entire_batch_on_donor_constraint_failure(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    batch_name = f"Atomic Failure {uuid4().hex}"
    async with postgres_session_factory() as session:
        user = await _add_user(session)
        segment = await _segment(session, "regular")
        store = PreviewStore(FakePreviewCache(), Clock(), 30)
        preview = StoredBatchPreview(
            original_filename="duplicates.csv",
            total_rows=2,
            valid_rows=2,
            invalid_rows=0,
            donors=[
                _stored_donor(2, segment),
                _stored_donor(3, segment),
            ],
            segment_breakdown=[],
            language_breakdown=[],
            errors=[],
            warnings=[],
            expires_at=store.expires_at(),
        )
        token = await store.save(preview)
        service = _upload_service(session, store)

        with pytest.raises(IntegrityError):
            await service.import_batch(
                BatchImportRequest(name=batch_name, preview_token=token),
                UserOut.model_validate(user),
            )

        batch_count = await session.scalar(
            select(func.count()).select_from(DonorBatch).where(DonorBatch.name == batch_name)
        )

    assert batch_count == 0
    assert (await store.get(token)).valid_rows == 2


def _upload_service(session: AsyncSession, store: PreviewStore) -> BatchUploadService:
    return BatchUploadService(
        session,
        DonorBatchRepository(session),
        DonorRepository(session),
        SegmentRepository(session),
        store,
        Clock(),
        max_size_mb=1,
        max_rows=100,
    )


async def _add_user(session: AsyncSession) -> User:
    user = User(
        email=f"batch-{uuid4().hex}@example.test",
        full_name="Batch Admin",
        password_hash="test-hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def _segment(session: AsyncSession, key: str) -> Segment:
    segment = await session.scalar(select(Segment).where(Segment.key == key))
    assert segment is not None
    return segment


async def _add_existing_donor(
    session: AsyncSession,
    user: User,
    segment: Segment,
    *,
    batch_name: str,
    phone: str,
) -> None:
    batch = DonorBatch(
        name=batch_name,
        original_filename="earlier.csv",
        uploaded_by_id=user.id,
        total_rows=1,
        valid_rows=1,
        invalid_rows=0,
        validation_report=[],
    )
    session.add(batch)
    await session.flush()
    session.add(
        Donor(
            batch_id=batch.id,
            full_name="Earlier Donor",
            phone_e164=phone,
            segment_id=segment.id,
            language=LanguageCode.EN,
        )
    )
    await session.flush()


def _stored_donor(row: int, segment: Segment) -> StoredDonorRow:
    return StoredDonorRow(
        row=row,
        name=f"Duplicate {row}",
        phone="+923221234567",
        segment=segment.key,
        segment_id=segment.id,
        language=LanguageCode.EN,
        city="Karachi",
        blood_group="O+",
        last_donation_date=date(2026, 1, 15),
    )


def _campaign_free_preview(store: PreviewStore, segment: Segment) -> StoredBatchPreview:
    donors = [
        _stored_donor_with_phone(2, segment, "+923221234561"),
        _stored_donor_with_phone(3, segment, "+923221234562"),
        _stored_donor_with_phone(4, segment, "+923221234563"),
    ]
    return StoredBatchPreview(
        original_filename="no-campaigns.csv",
        total_rows=len(donors),
        valid_rows=len(donors),
        invalid_rows=0,
        donors=donors,
        segment_breakdown=[],
        language_breakdown=[],
        errors=[],
        warnings=[],
        expires_at=store.expires_at(),
    )


def _stored_donor_with_phone(row: int, segment: Segment, phone: str) -> StoredDonorRow:
    donor = _stored_donor(row, segment)
    return donor.model_copy(update={"phone": phone})
