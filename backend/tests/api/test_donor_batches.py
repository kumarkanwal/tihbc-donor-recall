"""API tests for donor batch upload and browsing routes."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_batch_upload_service,
    get_current_user,
    get_donor_batch_query_service,
)
from app.core.errors import ValidationError
from app.main import app
from app.models.enums import LanguageCode, UserRole
from app.schemas.donor_batch import (
    BatchImportRequest,
    BatchPreview,
    DonorBatchDetail,
    DonorBatchOut,
    DonorBatchPage,
    DonorOut,
    DonorPage,
    UploadedBySummary,
    ValidationIssue,
)
from app.schemas.user import UserOut

NOW = datetime(2026, 10, 3, tzinfo=UTC)
BATCH_ID = uuid4()


class FakeBatchUploadService:
    """Return fixed upload results for route tests."""

    async def preview(self, filename: str, content: bytes) -> BatchPreview:
        assert filename == "donors.csv"
        assert content
        return BatchPreview(
            preview_token="preview-token",
            original_filename=filename,
            total_rows=1,
            valid_rows=1,
            invalid_rows=0,
            segment_breakdown=[],
            language_breakdown=[],
            sample_valid_rows=[],
            errors=[],
            warnings=[],
        )

    async def import_batch(
        self, request: BatchImportRequest, uploaded_by: UserOut
    ) -> DonorBatchOut:
        assert request.preview_token == "preview-token"
        assert request.name == "October Recall"
        return _batch(uploaded_by)


class EmptyBatchUploadService(FakeBatchUploadService):
    """Reject imports whose preview contains no valid donors."""

    async def import_batch(
        self, request: BatchImportRequest, uploaded_by: UserOut
    ) -> DonorBatchOut:
        del request, uploaded_by
        raise ValidationError("No valid donors to import")


class FakeBatchQueryService:
    """Return fixed batch and donor query results."""

    async def list_batches(
        self, *, search: str | None, sort: str, page: int, page_size: int
    ) -> DonorBatchPage:
        assert (search, sort, page, page_size) == ("October", "-created_at", 1, 20)
        return DonorBatchPage(items=[_batch(_admin())], total=1, page=1, page_size=20)

    async def get_batch(self, batch_id: UUID) -> DonorBatchDetail:
        assert batch_id == BATCH_ID
        return DonorBatchDetail(
            **_batch(_admin()).model_dump(),
            segment_breakdown=[],
            language_breakdown=[],
        )

    async def list_donors(
        self,
        batch_id: UUID,
        *,
        segment: str | None,
        language: LanguageCode | None,
        search: str | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> DonorPage:
        assert batch_id == BATCH_ID
        assert (segment, language, search, sort, page, page_size) == (
            "regular",
            LanguageCode.EN,
            "Ahsan",
            "full_name",
            1,
            20,
        )
        return DonorPage(
            items=[
                DonorOut(
                    id=uuid4(),
                    full_name="Ahsan Khan",
                    phone_e164="+92300*****67",
                    segment="regular",
                    language=LanguageCode.EN,
                    city="Karachi",
                    blood_group="O+",
                    last_donation_date=date(2026, 1, 15),
                    created_at=NOW,
                )
            ],
            total=1,
            page=1,
            page_size=20,
        )

    async def validation_report(self, batch_id: UUID) -> list[ValidationIssue]:
        assert batch_id == BATCH_ID
        return [ValidationIssue(row=3, field="phone", value="bad", reason="Invalid")]


def test_admin_can_download_preview_and_import() -> None:
    _override(_admin(), upload_service=FakeBatchUploadService())
    try:
        client = TestClient(app)
        sample = client.get("/api/v1/donor-batches/sample-file")
        preview = client.post(
            "/api/v1/donor-batches/preview",
            files={"file": ("donors.csv", b"name,phone,segment,language\n", "text/csv")},
        )
        imported = client.post(
            "/api/v1/donor-batches",
            json={"name": "  October Recall  ", "preview_token": "preview-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert sample.status_code == 200
    assert sample.headers["content-type"].startswith("text/csv")
    assert sample.text.count("\n") == 4
    assert preview.status_code == 200
    assert preview.json()["preview_token"] == "preview-token"
    assert imported.status_code == 201
    assert imported.json()["id"] == str(BATCH_ID)


@pytest.mark.parametrize(
    "payload",
    [
        {"preview_token": "preview-token"},
        {"name": "   ", "preview_token": "preview-token"},
        {"name": "x" * 121, "preview_token": "preview-token"},
    ],
)
def test_import_requires_trimmed_name_between_one_and_120_characters(
    payload: dict[str, str],
) -> None:
    _override(_admin(), upload_service=FakeBatchUploadService())
    try:
        response = TestClient(app).post("/api/v1/donor-batches", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_import_without_valid_donors_returns_validation_error() -> None:
    _override(_admin(), upload_service=EmptyBatchUploadService())
    try:
        response = TestClient(app).post(
            "/api/v1/donor-batches",
            json={"name": "Empty Batch", "preview_token": "preview-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "No valid donors to import",
        "details": {},
    }


def test_coordinator_is_forbidden_from_admin_upload_routes() -> None:
    _override(_coordinator(), upload_service=FakeBatchUploadService())
    try:
        client = TestClient(app)
        responses = [
            client.get("/api/v1/donor-batches/sample-file"),
            client.post(
                "/api/v1/donor-batches/preview",
                files={"file": ("donors.csv", b"data", "text/csv")},
            ),
            client.post(
                "/api/v1/donor-batches",
                json={"name": "Batch", "preview_token": "token"},
            ),
        ]
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [403, 403, 403]
    assert all(response.json()["error"]["code"] == "FORBIDDEN" for response in responses)


def test_coordinator_can_browse_batches_donors_and_report() -> None:
    _override(_coordinator(), query_service=FakeBatchQueryService())
    try:
        client = TestClient(app)
        batches = client.get("/api/v1/donor-batches?search=October")
        detail = client.get(f"/api/v1/donor-batches/{BATCH_ID}")
        donors = client.get(
            f"/api/v1/donor-batches/{BATCH_ID}/donors?segment=regular&language=en&search=Ahsan"
        )
        report = client.get(f"/api/v1/donor-batches/{BATCH_ID}/validation-report")
    finally:
        app.dependency_overrides.clear()

    assert batches.status_code == 200
    assert batches.json()["total"] == 1
    assert detail.status_code == 200
    assert donors.status_code == 200
    assert donors.json()["items"][0]["phone_e164"] == "+92300*****67"
    assert report.status_code == 200
    assert report.json()[0]["row"] == 3


def test_batch_routes_require_authentication() -> None:
    response = TestClient(app).get("/api/v1/donor-batches/sample-file")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def _override(
    user: UserOut,
    *,
    upload_service: FakeBatchUploadService | None = None,
    query_service: FakeBatchQueryService | None = None,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: user
    if upload_service is not None:
        app.dependency_overrides[get_batch_upload_service] = lambda: upload_service
    if query_service is not None:
        app.dependency_overrides[get_donor_batch_query_service] = lambda: query_service


def _batch(user: UserOut) -> DonorBatchOut:
    return DonorBatchOut(
        id=BATCH_ID,
        name="October Recall",
        original_filename="donors.csv",
        total_rows=1,
        valid_rows=1,
        invalid_rows=0,
        uploaded_by=UploadedBySummary(id=user.id, full_name=user.full_name),
        created_at=NOW,
        campaign_count=0,
    )


def _admin() -> UserOut:
    return _user(UserRole.ADMIN)


def _coordinator() -> UserOut:
    return _user(UserRole.COORDINATOR)


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(),
        email=f"{role.value}@example.test",
        full_name=role.value.title(),
        role=role,
        is_active=True,
    )
