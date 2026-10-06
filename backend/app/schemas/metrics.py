"""Dashboard metrics and report API schemas."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MetricsOverview(BaseModel):
    donors: int
    sent: int
    delivered: int
    read: int
    responded: int
    delivery_rate: float
    read_rate: float
    response_rate: float
    confirmed: int
    rescheduled: int
    declined: int
    escalated: int
    invalid_numbers: int
    undeliverable: int


class MetricsTimeseriesItem(BaseModel):
    date: date
    sent: int
    delivered: int
    read: int
    responded: int


class MetricsTimeseries(BaseModel):
    items: list[MetricsTimeseriesItem]


class MetricsResponseBreakdown(BaseModel):
    by_intent: dict[str, int]
    by_segment: dict[str, int]
    by_language: dict[str, int]


class DeclineReasonMetric(BaseModel):
    decline_reason: str
    count: int


class DeclineReasonMetrics(BaseModel):
    items: list[DeclineReasonMetric]


class CampaignMetricRow(BaseModel):
    campaign_id: UUID
    campaign_name: str
    batch_name: str
    status: str
    enrolled: int
    sent: int
    delivered: int
    read: int
    responded: int
    response_rate: float


class CampaignMetrics(BaseModel):
    items: list[CampaignMetricRow]


class InactiveNumberRow(BaseModel):
    id: UUID
    donor_name: str
    phone: str
    kind: Literal["invalid", "undeliverable"]
    reason: str
    batch_name: str
    campaign_name: str | None
    occurred_at: datetime


class InactiveNumberSummary(BaseModel):
    invalid: int
    undeliverable: int
    total: int


class InactiveNumberPage(BaseModel):
    items: list[InactiveNumberRow]
    total: int
    page: int
    page_size: int
    summary: InactiveNumberSummary
