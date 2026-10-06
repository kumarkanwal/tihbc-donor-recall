"""Dashboard metrics, report pagination, and CSV exports."""

import csv
from datetime import UTC, date, datetime, time, timedelta
from io import StringIO
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from app.repositories.inactive_report import InactiveReportRepository
from app.repositories.metrics import MetricsRepository, MetricsWindow
from app.schemas.metrics import (
    CampaignMetricRow,
    CampaignMetrics,
    DeclineReasonMetric,
    DeclineReasonMetrics,
    InactiveNumberPage,
    InactiveNumberRow,
    InactiveNumberSummary,
    MetricsOverview,
    MetricsResponseBreakdown,
    MetricsTimeseries,
    MetricsTimeseriesItem,
)

ReportName = Literal["inactive-numbers", "response-breakdown", "campaigns"]


class MetricsService:
    """Build contract views directly from operational source records."""

    def __init__(
        self,
        repository: MetricsRepository,
        inactive_repository: InactiveReportRepository,
        timezone_display: str,
    ) -> None:
        self._repository = repository
        self._inactive_repository = inactive_repository
        self._timezone = ZoneInfo(timezone_display)

    def window(
        self, campaign_id: UUID | None, from_date: date | None, to_date: date | None
    ) -> MetricsWindow:
        """Interpret inclusive report dates in the configured display timezone."""
        from_at = self._utc_start(from_date) if from_date else None
        to_at = self._utc_start(to_date + timedelta(days=1)) if to_date else None
        return MetricsWindow(campaign_id, from_at, to_at)

    async def overview(self, window: MetricsWindow) -> MetricsOverview:
        counts = await self._repository.overview(window)
        inactive = await self._inactive_repository.inactive_numbers(window)
        return MetricsOverview(
            **counts.__dict__,
            invalid_numbers=sum(row.kind == "invalid" for row in inactive),
            delivery_rate=_percentage(counts.delivered, counts.sent),
            read_rate=_percentage(counts.read, counts.delivered),
            response_rate=_percentage(counts.responded, counts.donors),
        )

    async def timeseries(self, window: MetricsWindow) -> MetricsTimeseries:
        rows = await self._repository.timeseries(window)
        return MetricsTimeseries(
            items=[
                MetricsTimeseriesItem(
                    date=day,
                    sent=counts.get("sent", 0),
                    delivered=counts.get("delivered", 0),
                    read=counts.get("read", 0),
                    responded=counts.get("responded", 0),
                )
                for day, counts in sorted(rows.items())
            ]
        )

    async def response_breakdown(self, window: MetricsWindow) -> MetricsResponseBreakdown:
        by_intent, by_segment, by_language = await self._repository.response_breakdown(window)
        return MetricsResponseBreakdown(
            by_intent=by_intent,
            by_segment=by_segment,
            by_language=by_language,
        )

    async def decline_reasons(self, window: MetricsWindow) -> DeclineReasonMetrics:
        rows = await self._repository.decline_reasons(window)
        return DeclineReasonMetrics(
            items=[
                DeclineReasonMetric(decline_reason=reason, count=count)
                for reason, count in sorted(rows.items())
            ]
        )

    async def campaigns(self, window: MetricsWindow) -> CampaignMetrics:
        records = await self._repository.campaign_metrics(window)
        return CampaignMetrics(
            items=[
                CampaignMetricRow(
                    **record.__dict__,
                    response_rate=_percentage(record.responded, record.enrolled),
                )
                for record in records
            ]
        )

    async def inactive_numbers(
        self, window: MetricsWindow, *, page: int, page_size: int
    ) -> InactiveNumberPage:
        records = await self._inactive_repository.inactive_numbers(window)
        invalid = sum(record.kind == "invalid" for record in records)
        undeliverable = len(records) - invalid
        start = (page - 1) * page_size
        return InactiveNumberPage(
            items=[
                InactiveNumberRow.model_validate(record.__dict__)
                for record in records[start : start + page_size]
            ],
            total=len(records),
            page=page,
            page_size=page_size,
            summary=InactiveNumberSummary(
                invalid=invalid,
                undeliverable=undeliverable,
                total=len(records),
            ),
        )

    async def export_csv(self, report: ReportName, window: MetricsWindow) -> str:
        """Render one documented report as CSV."""
        output = StringIO(newline="")
        writer = csv.writer(output)
        if report == "inactive-numbers":
            page = await self.inactive_numbers(window, page=1, page_size=100_000)
            writer.writerow(
                [
                    "donor_name",
                    "phone",
                    "kind",
                    "reason",
                    "batch_name",
                    "campaign_name",
                    "occurred_at",
                ]
            )
            for inactive_row in page.items:
                writer.writerow(
                    [
                        inactive_row.donor_name,
                        inactive_row.phone,
                        inactive_row.kind,
                        inactive_row.reason,
                        inactive_row.batch_name,
                        inactive_row.campaign_name or "",
                        inactive_row.occurred_at.isoformat(),
                    ]
                )
        elif report == "response-breakdown":
            breakdown = await self.response_breakdown(window)
            writer.writerow(["dimension", "group", "count"])
            for dimension, values in (
                ("intent", breakdown.by_intent),
                ("segment", breakdown.by_segment),
                ("language", breakdown.by_language),
            ):
                for group, count in sorted(values.items()):
                    writer.writerow([dimension, group, count])
        else:
            rows = await self.campaigns(window)
            writer.writerow(
                [
                    "campaign",
                    "batch",
                    "status",
                    "enrolled",
                    "sent",
                    "delivered",
                    "read",
                    "responded",
                    "response_rate",
                ]
            )
            for campaign_row in rows.items:
                writer.writerow(
                    [
                        campaign_row.campaign_name,
                        campaign_row.batch_name,
                        campaign_row.status,
                        campaign_row.enrolled,
                        campaign_row.sent,
                        campaign_row.delivered,
                        campaign_row.read,
                        campaign_row.responded,
                        campaign_row.response_rate,
                    ]
                )
        return output.getvalue()

    def _utc_start(self, value: date) -> datetime:
        return datetime.combine(value, time.min, self._timezone).astimezone(UTC)


def _percentage(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 1) if denominator else 0.0
