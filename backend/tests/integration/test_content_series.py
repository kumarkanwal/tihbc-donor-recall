"""PostgreSQL HTTP coverage for content-series workflows."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_current_user
from app.core.db import get_db
from app.main import app
from app.models.campaign import Campaign
from app.models.donor import DonorBatch
from app.models.enums import CampaignStatus, LanguageCode, SeriesKind, UserRole
from app.models.series import ContentSeries
from app.models.user import User
from app.schemas.user import UserOut

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_http_create_activate_and_filtered_list_flow(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    series_name = f"Regular Donor Recall {uuid4().hex}"
    async with postgres_session_factory() as session:
        user = await _add_user(session)
        _override_database(session, user)
        try:
            async with _client() as client:
                created = await _create_series(client, name=series_name)
                series_id = created.json()["id"]
                step = await client.post(
                    f"/api/v1/content-series/{series_id}/steps",
                    json=_step_payload(
                        0,
                        "Hello {{donor_name}} on {{appointment_date}}",
                        "سلام {{donor_name}}، {{appointment_date}}",
                    ),
                )
                activated = await client.post(
                    f"/api/v1/content-series/{series_id}/actions/activate"
                )
                preview = await client.post(
                    f"/api/v1/content-series/{series_id}/preview",
                    json={"step_id": step.json()["id"], "language": "ur"},
                )
                listed = await client.get(
                    "/api/v1/content-series",
                    params={
                        "kind": "primary",
                        "status": "active",
                        "tag": "regular",
                        "language": "ur",
                        "search": series_name,
                    },
                )
        finally:
            app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["tags"] == ["recall", "regular"]
    assert step.status_code == 201
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    assert preview.status_code == 200
    assert "Ahmed Raza" in preview.json()["body"]
    assert "صبح ۱۰ بجے" in preview.json()["body"]
    assert preview.json()["buttons"] == [{"id": "btn_confirm", "label": "تصدیق کریں"}]
    assert listed.status_code == 200
    listed_items = {item["id"]: item for item in listed.json()["items"]}
    assert series_id in listed_items
    assert listed_items[series_id]["step_count"] == 1


@pytest.mark.asyncio
async def test_http_reorder_delete_duplicate_and_activation_errors(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        user = await _add_user(session)
        _override_database(session, user)
        try:
            async with _client() as client:
                series_id = (await _create_series(client)).json()["id"]
                steps = [
                    await client.post(
                        f"/api/v1/content-series/{series_id}/steps",
                        json=_step_payload(index, f"English {index}", f"Urdu {index}"),
                    )
                    for index in range(3)
                ]
                step_ids = [response.json()["id"] for response in steps]
                updated = await client.patch(
                    f"/api/v1/content-series/{series_id}/steps/{step_ids[0]}",
                    json={"delay_days": 4},
                )
                reordered = await client.post(
                    f"/api/v1/content-series/{series_id}/steps/actions/reorder",
                    json={"step_ids": list(reversed(step_ids))},
                )
                deleted = await client.delete(
                    f"/api/v1/content-series/{series_id}/steps/{step_ids[1]}"
                )
                duplicated = await client.post(
                    f"/api/v1/content-series/{series_id}/actions/duplicate"
                )
                copy_id = duplicated.json()["id"]
                archived = await client.post(f"/api/v1/content-series/{copy_id}/actions/archive")
                archived_edit = await client.patch(
                    f"/api/v1/content-series/{copy_id}", json={"name": "Not allowed"}
                )
                archived_activate = await client.post(
                    f"/api/v1/content-series/{copy_id}/actions/activate"
                )
                incomplete_id = (await _create_series(client, name="Incomplete")).json()["id"]
                await client.post(
                    f"/api/v1/content-series/{incomplete_id}/steps",
                    json={
                        "delay_days": 0,
                        "category": "utility",
                        "media_type": "image",
                        "contents": [{"language": "en", "body": ""}],
                        "buttons": [],
                    },
                )
                activation = await client.post(
                    f"/api/v1/content-series/{incomplete_id}/actions/activate"
                )
        finally:
            app.dependency_overrides.clear()

    assert updated.json()["delay_days"] == 4
    assert [item["id"] for item in reordered.json()["steps"]] == list(reversed(step_ids))
    assert [item["step_order"] for item in deleted.json()["steps"]] == [1, 2]
    assert duplicated.status_code == 201
    assert duplicated.json()["name"] == "Regular Donor Recall (copy)"
    assert duplicated.json()["status"] == "draft"
    assert len(duplicated.json()["steps"]) == 2
    assert archived.json()["status"] == "archived"
    assert archived_edit.status_code == 409
    assert archived_activate.status_code == 409
    assert activation.status_code == 422
    problems = activation.json()["error"]["details"]["problems"]
    assert {(item["language"], item["field"]) for item in problems} == {
        ("en", "body"),
        ("ur", "body"),
        (None, "media_url"),
    }


@pytest.mark.asyncio
async def test_http_edit_is_blocked_by_scheduled_campaign(
    postgres_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with postgres_session_factory() as session:
        user = await _add_user(session)
        primary, secondary, batch = _campaign_models(user)
        session.add_all((primary, secondary, batch))
        await session.flush()
        session.add(
            Campaign(
                name="Scheduled Campaign",
                batch_id=batch.id,
                primary_series_id=primary.id,
                secondary_series_id=secondary.id,
                status=CampaignStatus.SCHEDULED,
                start_at=datetime(2026, 10, 5, tzinfo=UTC),
                created_by_id=user.id,
            )
        )
        await session.commit()
        _override_database(session, user)
        try:
            async with _client() as client:
                response = await client.patch(
                    f"/api/v1/content-series/{primary.id}",
                    json={"name": "Blocked Edit"},
                )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


def _override_database(session: AsyncSession, user: User) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: UserOut.model_validate(user)


async def _create_series(client: AsyncClient, *, name: str = "Regular Donor Recall") -> Response:
    return await client.post(
        "/api/v1/content-series",
        json={
            "name": name,
            "description": "Bilingual recall",
            "kind": "primary",
            "languages": ["en", "ur"],
            "response_window_hours": 48,
            "tag_names": ["Regular", "Recall"],
        },
    )


def _step_payload(delay_days: int, english: str, urdu: str) -> dict[str, object]:
    return {
        "delay_days": delay_days,
        "category": "utility",
        "media_type": "none",
        "contents": [
            {"language": "en", "body": english},
            {"language": "ur", "body": urdu},
        ],
        "buttons": [
            {
                "id": "btn_confirm",
                "intent": "confirm",
                "labels": {"en": "Confirm", "ur": "تصدیق کریں"},
            }
        ],
    }


async def _add_user(session: AsyncSession) -> User:
    user = User(
        email=f"series-{uuid4().hex}@example.test",
        full_name="Series Admin",
        password_hash="test-hash",
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


def _campaign_models(user: User) -> tuple[ContentSeries, ContentSeries, DonorBatch]:
    primary = ContentSeries(
        name="Primary",
        kind=SeriesKind.PRIMARY,
        languages=[LanguageCode.EN],
        created_by_id=user.id,
    )
    secondary = ContentSeries(
        name="Secondary",
        kind=SeriesKind.SECONDARY,
        languages=[LanguageCode.EN],
        created_by_id=user.id,
    )
    batch = DonorBatch(
        name="Campaign Batch",
        original_filename="campaign.csv",
        uploaded_by_id=user.id,
        total_rows=1,
        valid_rows=1,
        invalid_rows=0,
        validation_report=[],
    )
    return primary, secondary, batch
