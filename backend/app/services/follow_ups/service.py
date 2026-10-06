"""Coordinator follow-up queries and workflow mutations."""

import csv
from io import StringIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.enums import FollowUpOutcome, FollowUpStatus, FollowUpType
from app.models.follow_up import FollowUpActivity, FollowUpItem
from app.repositories.follow_up import FollowUpFilters, FollowUpRepository
from app.repositories.user import UserRepository
from app.schemas.follow_up import (
    FollowUpDetail,
    FollowUpInboxSummary,
    FollowUpNoteCreate,
    FollowUpPage,
    FollowUpResolve,
    FollowUpUpdate,
)
from app.schemas.user import UserOut
from app.services.events.base import EventPublisher
from app.services.follow_ups.mappers import follow_up_detail, follow_up_list_item
from app.services.follow_ups.payloads import follow_up_created_payload
from app.ws.events import EventType


class FollowUpService:
    """Serve the inbox and apply auditable coordinator changes."""

    def __init__(
        self,
        session: AsyncSession,
        repository: FollowUpRepository,
        users: UserRepository,
        clock: Clock,
        publisher: EventPublisher,
    ) -> None:
        self._session = session
        self._repository = repository
        self._users = users
        self._clock = clock
        self._publisher = publisher

    async def list(self, filters: FollowUpFilters, *, page: int, page_size: int) -> FollowUpPage:
        """Return one filtered inbox page."""
        result = await self._repository.list_filtered(filters, page=page, page_size=page_size)
        return FollowUpPage(
            items=[follow_up_list_item(item) for item in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def summary(self, filters: FollowUpFilters) -> FollowUpInboxSummary:
        """Return complete enum-keyed counts for tabs and status filters."""
        total, by_type, by_status = await self._repository.summary(filters)
        return FollowUpInboxSummary(
            total=total,
            by_type={value: by_type.get(value, 0) for value in FollowUpType},
            by_status={value: by_status.get(value, 0) for value in FollowUpStatus},
        )

    async def get(self, item_id: UUID) -> FollowUpDetail:
        """Return one complete follow-up view."""
        return follow_up_detail(await self._required(item_id))

    async def update(
        self, item_id: UUID, request: FollowUpUpdate, current_user: UserOut
    ) -> FollowUpDetail:
        """Update selected workflow fields and record each changed value."""
        item = await self._required(item_id, for_update=True)
        activities: list[FollowUpActivity] = []
        if request.status is not None and request.status != item.status:
            activities.append(
                self._activity(
                    item,
                    current_user,
                    "status_changed",
                    f"{item.status.value} -> {request.status.value}",
                )
            )
            item.status = request.status
        if request.priority is not None and request.priority != item.priority:
            activities.append(
                self._activity(
                    item,
                    current_user,
                    "priority_changed",
                    f"{item.priority.value} -> {request.priority.value}",
                )
            )
            item.priority = request.priority
        if request.assigned_to_id is not None and request.assigned_to_id != item.assigned_to_id:
            if await self._users.get(request.assigned_to_id) is None:
                raise ValidationError(
                    "Assigned user does not exist", {"assigned_to_id": "not_found"}
                )
            item.assigned_to_id = request.assigned_to_id
            activities.append(self._activity(item, current_user, "assigned", None))
        for activity in activities:
            await self._repository.add_activity(activity)
        return await self._commit_and_detail(item)

    async def add_note(
        self, item_id: UUID, request: FollowUpNoteCreate, current_user: UserOut
    ) -> FollowUpDetail:
        """Append a coordinator note and publish the updated item."""
        item = await self._required(item_id, for_update=True)
        await self._repository.add_activity(
            self._activity(item, current_user, "note", request.note.strip())
        )
        return await self._commit_and_detail(item)

    async def resolve(
        self, item_id: UUID, request: FollowUpResolve, current_user: UserOut
    ) -> FollowUpDetail:
        """Resolve one item with its documented outcome."""
        item = await self._required(item_id, for_update=True)
        if item.status == FollowUpStatus.DONE:
            raise ValidationError("Follow-up is already resolved", {"status": "done"})
        item.status = FollowUpStatus.DONE
        item.outcome = FollowUpOutcome(request.outcome.value)
        item.resolved_at = self._clock.now()
        item.resolved_by_id = current_user.id
        await self._repository.add_activity(
            self._activity(
                item, current_user, "resolved", request.note.strip() if request.note else None
            )
        )
        return await self._commit_and_detail(item)

    async def export_csv(self, filters: FollowUpFilters) -> str:
        """Return current filtered inbox rows as UTF-8 CSV text."""
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(
            [
                "donor_name",
                "phone",
                "campaign",
                "type",
                "status",
                "priority",
                "assigned_to",
                "latest_reply",
                "updated_at",
            ]
        )
        for item in await self._repository.list_for_export(filters):
            row = follow_up_list_item(item)
            writer.writerow(
                [
                    row.donor.name,
                    row.donor.phone,
                    row.campaign.name,
                    row.type.value,
                    row.status.value,
                    row.priority.value,
                    row.assigned_to.full_name if row.assigned_to else "",
                    row.latest_reply.body if row.latest_reply else "",
                    row.updated_at.isoformat(),
                ]
            )
        return output.getvalue()

    async def _required(self, item_id: UUID, *, for_update: bool = False) -> FollowUpItem:
        item = await self._repository.get_full(item_id, for_update=for_update)
        if item is None:
            raise NotFoundError("Follow-up not found")
        return item

    @staticmethod
    def _activity(
        item: FollowUpItem, user: UserOut, action: str, note: str | None
    ) -> FollowUpActivity:
        return FollowUpActivity(
            follow_up_id=item.id,
            user_id=user.id,
            action=action,
            note=note,
        )

    async def _commit_and_detail(self, item: FollowUpItem) -> FollowUpDetail:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        refreshed = await self._required(item.id)
        payload = follow_up_created_payload(refreshed)
        detail = follow_up_detail(refreshed)
        await self._session.rollback()
        await self._publisher.publish(EventType.FOLLOWUP_UPDATED.value, payload)
        return detail
