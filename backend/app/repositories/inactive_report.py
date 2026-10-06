"""Query upload-invalid and sending-undeliverable number rows."""

from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import Select, String, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, Enrollment
from app.models.donor import Donor, DonorBatch
from app.models.enums import EnrollmentStatus
from app.models.message import Message
from app.repositories.metrics import DateColumn, MetricsWindow


@dataclass(frozen=True)
class InactiveNumberRecord:
    id: UUID
    donor_name: str
    phone: str
    kind: str
    reason: str
    batch_name: str
    campaign_name: str | None
    occurred_at: datetime


class InactiveReportRepository:
    """Combine inactive-number sources without persisted report rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def inactive_numbers(self, window: MetricsWindow) -> list[InactiveNumberRecord]:
        """Return invalid uploads and undeliverable enrollments newest first."""
        records = await self._invalid_rows(window)
        failed_reason = (
            select(Message.failed_reason)
            .where(
                Message.enrollment_id == Enrollment.id,
                Message.failed_reason.is_not(None),
            )
            .order_by(Message.updated_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        statement = (
            select(Enrollment, Donor, DonorBatch.name, Campaign.name, failed_reason)
            .join(Donor, Enrollment.donor_id == Donor.id)
            .join(DonorBatch, Donor.batch_id == DonorBatch.id)
            .join(Campaign, Enrollment.campaign_id == Campaign.id)
            .where(Enrollment.status == EnrollmentStatus.UNDELIVERABLE)
        )
        if window.campaign_id:
            statement = statement.where(Enrollment.campaign_id == window.campaign_id)
        statement = _dated(statement, Enrollment.updated_at, window)
        for row in await self._session.execute(statement):
            enrollment = cast(Enrollment, row[0])
            donor = cast(Donor, row[1])
            records.append(
                InactiveNumberRecord(
                    id=enrollment.id,
                    donor_name=donor.full_name,
                    phone=donor.phone_e164,
                    kind="undeliverable",
                    reason=cast(str | None, row[4]) or "Message could not be delivered",
                    batch_name=cast(str, row[2]),
                    campaign_name=cast(str, row[3]),
                    occurred_at=enrollment.updated_at,
                )
            )
        return sorted(records, key=lambda value: (value.occurred_at, value.id), reverse=True)

    async def _invalid_rows(self, window: MetricsWindow) -> list[InactiveNumberRecord]:
        if window.campaign_id:
            statement = (
                select(DonorBatch, Campaign.name)
                .join(Campaign, Campaign.batch_id == DonorBatch.id)
                .where(Campaign.id == window.campaign_id)
            )
        else:
            statement = select(DonorBatch, literal(None, String).label("campaign_name"))
        statement = _dated(statement, DonorBatch.created_at, window)
        records: list[InactiveNumberRecord] = []
        for batch, campaign_name in await self._session.execute(statement):
            for index, issue in enumerate(batch.validation_report):
                if issue.get("field") != "phone":
                    continue
                row_number = issue.get("row", index + 2)
                records.append(
                    InactiveNumberRecord(
                        id=uuid5(NAMESPACE_URL, f"invalid:{batch.id}:{row_number}:{index}"),
                        donor_name=f"Upload row {row_number}",
                        phone=str(issue.get("value") or "Unavailable"),
                        kind="invalid",
                        reason=str(issue.get("reason") or "Invalid phone number"),
                        batch_name=batch.name,
                        campaign_name=campaign_name,
                        occurred_at=batch.created_at,
                    )
                )
        return records


def _dated[*RowT](
    statement: Select[*RowT], column: DateColumn, window: MetricsWindow
) -> Select[*RowT]:
    if window.from_at:
        statement = statement.where(column >= window.from_at)
    if window.to_at:
        statement = statement.where(column < window.to_at)
    return statement
