"""Query-computed dashboard metrics and report rows."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, Select, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Subquery

from app.models.campaign import Campaign, Enrollment
from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import EnrollmentStatus, MessageDirection
from app.models.message import Message
from app.models.response import DonorResponse

DateColumn = (
    InstrumentedAttribute[datetime]
    | InstrumentedAttribute[datetime | None]
    | ColumnElement[datetime]
    | ColumnElement[datetime | None]
)


@dataclass(frozen=True)
class MetricsWindow:
    campaign_id: UUID | None
    from_at: datetime | None
    to_at: datetime | None


@dataclass(frozen=True)
class OverviewCounts:
    donors: int
    sent: int
    delivered: int
    read: int
    responded: int
    confirmed: int
    rescheduled: int
    declined: int
    escalated: int
    undeliverable: int


@dataclass(frozen=True)
class CampaignMetricRecord:
    campaign_id: UUID
    campaign_name: str
    batch_name: str
    status: str
    enrolled: int
    sent: int
    delivered: int
    read: int
    responded: int


class MetricsRepository:
    """Read operational aggregates without persisted counter columns."""

    def __init__(self, session: AsyncSession, timezone_display: str) -> None:
        self._session = session
        self._timezone = timezone_display

    async def overview(self, window: MetricsWindow) -> OverviewCounts:
        """Compute all headline counters from source records."""
        donors = await self._enrollment_count(window, Enrollment.created_at)
        sent = await self._message_count(window, Message.sent_at)
        delivered = await self._message_count(window, Message.delivered_at)
        read = await self._message_count(window, Message.read_at)
        responded = await self._enrollment_count(window, Enrollment.responded_at)
        statuses = await self._status_counts(window)
        return OverviewCounts(
            donors=donors,
            sent=sent,
            delivered=delivered,
            read=read,
            responded=responded,
            confirmed=statuses.get(EnrollmentStatus.CONFIRMED, 0),
            rescheduled=statuses.get(EnrollmentStatus.RESCHEDULED, 0),
            declined=statuses.get(EnrollmentStatus.DECLINED, 0),
            escalated=statuses.get(EnrollmentStatus.ESCALATED, 0),
            undeliverable=statuses.get(EnrollmentStatus.UNDELIVERABLE, 0),
        )

    async def timeseries(self, window: MetricsWindow) -> dict[date, dict[str, int]]:
        """Group sent, delivery, read, and response activity by local demo date."""
        result: dict[date, dict[str, int]] = {}
        for label, column in (
            ("sent", Message.sent_at),
            ("delivered", Message.delivered_at),
            ("read", Message.read_at),
        ):
            for day, count in await self._message_daily(window, column):
                result.setdefault(day, {})[label] = count
        for day, count in await self._enrollment_daily(window, Enrollment.responded_at):
            result.setdefault(day, {})["responded"] = count
        return result

    async def response_breakdown(
        self, window: MetricsWindow
    ) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Return response counts by intent, donor segment, and language."""
        base = (
            select(DonorResponse)
            .join(Enrollment, DonorResponse.enrollment_id == Enrollment.id)
            .join(Donor, Enrollment.donor_id == Donor.id)
        )
        base = self._response_filtered(base, window)
        intent_rows = await self._session.execute(
            base.with_only_columns(DonorResponse.intent, func.count()).group_by(
                DonorResponse.intent
            )
        )
        segment_rows = await self._session.execute(
            base.join(Segment, Donor.segment_id == Segment.id)
            .with_only_columns(Segment.key, func.count())
            .group_by(Segment.key)
        )
        language_rows = await self._session.execute(
            base.with_only_columns(Donor.language, func.count()).group_by(Donor.language)
        )
        return (
            {key.value: count for key, count in intent_rows},
            dict(segment_rows.all()),
            {key.value: count for key, count in language_rows},
        )

    async def decline_reasons(self, window: MetricsWindow) -> dict[str, int]:
        """Return non-null classified decline reasons."""
        statement = (
            select(DonorResponse.decline_reason, func.count())
            .join(Enrollment, DonorResponse.enrollment_id == Enrollment.id)
            .where(DonorResponse.decline_reason.is_not(None))
            .group_by(DonorResponse.decline_reason)
        )
        statement = self._response_filtered(statement, window)
        rows = await self._session.execute(statement)
        return {reason.value: count for reason, count in rows if reason is not None}

    async def campaign_metrics(self, window: MetricsWindow) -> list[CampaignMetricRecord]:
        """Compute comparison rows with per-campaign scalar subqueries."""
        enrolled = self._campaign_enrollment_counts(window, Enrollment.created_at)
        responded = self._campaign_enrollment_counts(window, Enrollment.responded_at)
        sent = self._campaign_message_counts(window, Message.sent_at)
        delivered = self._campaign_message_counts(window, Message.delivered_at)
        read = self._campaign_message_counts(window, Message.read_at)
        statement = (
            select(
                Campaign.id,
                Campaign.name,
                DonorBatch.name,
                Campaign.status,
                func.coalesce(enrolled.c.count, 0),
                func.coalesce(sent.c.count, 0),
                func.coalesce(delivered.c.count, 0),
                func.coalesce(read.c.count, 0),
                func.coalesce(responded.c.count, 0),
            )
            .join(DonorBatch, Campaign.batch_id == DonorBatch.id)
            .outerjoin(enrolled, enrolled.c.campaign_id == Campaign.id)
            .outerjoin(sent, sent.c.campaign_id == Campaign.id)
            .outerjoin(delivered, delivered.c.campaign_id == Campaign.id)
            .outerjoin(read, read.c.campaign_id == Campaign.id)
            .outerjoin(responded, responded.c.campaign_id == Campaign.id)
            .order_by(Campaign.created_at.desc(), Campaign.id)
        )
        if window.campaign_id:
            statement = statement.where(Campaign.id == window.campaign_id)
        records: list[CampaignMetricRecord] = []
        for (
            campaign_id,
            campaign_name,
            batch_name,
            status,
            enrolled_count,
            sent_count,
            delivered_count,
            read_count,
            responded_count,
        ) in await self._session.execute(statement):
            records.append(
                CampaignMetricRecord(
                    campaign_id,
                    campaign_name,
                    batch_name,
                    status.value,
                    enrolled_count,
                    sent_count,
                    delivered_count,
                    read_count,
                    responded_count,
                )
            )
        return records

    async def _enrollment_count(self, window: MetricsWindow, column: DateColumn) -> int:
        statement = select(func.count(Enrollment.id)).where(column.is_not(None))
        statement = self._enrollment_filtered(statement, window, column)
        return int(await self._session.scalar(statement) or 0)

    async def _message_count(self, window: MetricsWindow, column: DateColumn) -> int:
        statement = (
            select(func.count(Message.id))
            .join(Enrollment, Message.enrollment_id == Enrollment.id)
            .where(Message.direction == MessageDirection.OUTBOUND, column.is_not(None))
        )
        statement = self._dated(statement, column, window)
        if window.campaign_id:
            statement = statement.where(Enrollment.campaign_id == window.campaign_id)
        return int(await self._session.scalar(statement) or 0)

    async def _status_counts(self, window: MetricsWindow) -> dict[EnrollmentStatus, int]:
        event_at = func.coalesce(Enrollment.responded_at, Enrollment.updated_at)
        statement = select(Enrollment.status, func.count()).group_by(Enrollment.status)
        statement = self._enrollment_filtered(statement, window, event_at)
        return dict((await self._session.execute(statement)).all())

    async def _message_daily(
        self, window: MetricsWindow, column: DateColumn
    ) -> list[tuple[date, int]]:
        day = cast(func.timezone(self._timezone, column), Date)
        statement = (
            select(day, func.count(Message.id))
            .join(Enrollment, Message.enrollment_id == Enrollment.id)
            .where(Message.direction == MessageDirection.OUTBOUND, column.is_not(None))
            .group_by(day)
            .order_by(day)
        )
        statement = self._dated(statement, column, window)
        if window.campaign_id:
            statement = statement.where(Enrollment.campaign_id == window.campaign_id)
        return list((await self._session.execute(statement)).all())

    async def _enrollment_daily(
        self, window: MetricsWindow, column: DateColumn
    ) -> list[tuple[date, int]]:
        day = cast(func.timezone(self._timezone, column), Date)
        statement = select(day, func.count(Enrollment.id)).where(column.is_not(None)).group_by(day)
        statement = self._enrollment_filtered(statement, window, column)
        return list((await self._session.execute(statement)).all())

    def _campaign_enrollment_counts(self, window: MetricsWindow, column: DateColumn) -> Subquery:
        statement = select(Enrollment.campaign_id, func.count(Enrollment.id).label("count"))
        statement = self._dated(statement, column, window).where(column.is_not(None))
        return statement.group_by(Enrollment.campaign_id).subquery()

    def _campaign_message_counts(self, window: MetricsWindow, column: DateColumn) -> Subquery:
        statement = (
            select(Enrollment.campaign_id, func.count(Message.id).label("count"))
            .join(Enrollment, Message.enrollment_id == Enrollment.id)
            .where(Message.direction == MessageDirection.OUTBOUND, column.is_not(None))
        )
        statement = self._dated(statement, column, window)
        return statement.group_by(Enrollment.campaign_id).subquery()

    def _response_filtered[*RowT](
        self, statement: Select[*RowT], window: MetricsWindow
    ) -> Select[*RowT]:
        if window.campaign_id:
            statement = statement.where(Enrollment.campaign_id == window.campaign_id)
        return self._dated(statement, DonorResponse.created_at, window)

    def _enrollment_filtered[*RowT](
        self, statement: Select[*RowT], window: MetricsWindow, column: DateColumn
    ) -> Select[*RowT]:
        if window.campaign_id:
            statement = statement.where(Enrollment.campaign_id == window.campaign_id)
        return self._dated(statement, column, window)

    @staticmethod
    def _dated[*RowT](
        statement: Select[*RowT], column: DateColumn, window: MetricsWindow
    ) -> Select[*RowT]:
        if window.from_at:
            statement = statement.where(column >= window.from_at)
        if window.to_at:
            statement = statement.where(column < window.to_at)
        return statement
