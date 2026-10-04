"""Role and media-route tests for content-series APIs."""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import (
    get_content_series_query_service,
    get_current_user,
    get_media_service,
)
from app.core.config import get_settings
from app.main import app, create_app
from app.models.enums import UserRole
from app.schemas.content_series import ContentSeriesPage
from app.schemas.user import UserOut
from app.services.media_service import MediaService


class EmptySeriesQueryService:
    """Return an empty content-series page for route tests."""

    async def list_series(self, **filters: object) -> ContentSeriesPage:
        assert filters["page"] == 1
        return ContentSeriesPage(items=[], total=0, page=1, page_size=20)


def test_coordinator_can_list_but_cannot_mutate_or_upload() -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.COORDINATOR)
    app.dependency_overrides[get_content_series_query_service] = lambda: EmptySeriesQueryService()
    try:
        client = TestClient(app)
        listed = client.get("/api/v1/content-series")
        created = client.post(
            "/api/v1/content-series",
            json={"name": "Blocked", "kind": "primary", "languages": ["en"]},
        )
        uploaded = client.post(
            "/api/v1/media",
            files={"file": ("image.png", b"\x89PNG\r\n\x1a\npayload", "image/png")},
        )
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 200
    assert listed.json()["items"] == []
    assert created.status_code == 403
    assert uploaded.status_code == 403


def test_admin_media_upload_uses_detected_content_type(tmp_path: Path) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(UserRole.ADMIN)
    app.dependency_overrides[get_media_service] = lambda: MediaService(
        tmp_path, "http://testserver/media"
    )
    try:
        response = TestClient(app).post(
            "/api/v1/media",
            files={"file": ("wrong.txt", b"\x89PNG\r\n\x1a\npayload", "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["media_type"] == "image"
    assert response.json()["url"].endswith(".png")


def test_static_media_mount_serves_stored_files(tmp_path: Path) -> None:
    content = b"\x89PNG\r\n\x1a\npayload"
    (tmp_path / "asset.png").write_bytes(content)
    settings = get_settings().model_copy(update={"media_storage_dir": tmp_path})

    response = TestClient(create_app(settings)).get("/media/asset.png")

    assert response.status_code == 200
    assert response.content == content


def test_content_series_and_media_routes_require_authentication() -> None:
    client = TestClient(app)

    assert client.get("/api/v1/content-series").status_code == 401
    assert client.post("/api/v1/media").status_code == 401


def _user(role: UserRole) -> UserOut:
    return UserOut(
        id=uuid4(),
        email=f"{role.value}@example.test",
        full_name=role.value.title(),
        role=role,
        is_active=True,
    )
