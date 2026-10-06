"""Dashboard metrics and report routes."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_metrics_service, require_role
from app.models.enums import UserRole
from app.repositories.metrics import MetricsWindow
from app.schemas.metrics import (
    CampaignMetrics,
    DeclineReasonMetrics,
    InactiveNumberPage,
    MetricsOverview,
    MetricsResponseBreakdown,
    MetricsTimeseries,
)
from app.schemas.user import UserOut
from app.services.metrics_service import MetricsService, ReportName

metrics_router = APIRouter(prefix="/metrics", tags=["Metrics"])
reports_router = APIRouter(prefix="/reports", tags=["Reports"])
staff_access = require_role(UserRole.ADMIN, UserRole.COORDINATOR)


def _window(
    service: MetricsService,
    campaign_id: UUID | None,
    from_date: date | None,
    to_date: date | None,
) -> MetricsWindow:
    return service.window(campaign_id, from_date, to_date)


@metrics_router.get("/overview", response_model=MetricsOverview, summary="Get metrics overview")
async def metrics_overview(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> MetricsOverview:
    del current_user
    return await service.overview(_window(service, campaign_id, from_date, to_date))


@metrics_router.get("/timeseries", response_model=MetricsTimeseries, summary="Get daily metrics")
async def metrics_timeseries(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> MetricsTimeseries:
    del current_user
    return await service.timeseries(_window(service, campaign_id, from_date, to_date))


@metrics_router.get(
    "/response-breakdown",
    response_model=MetricsResponseBreakdown,
    summary="Get response breakdown",
)
async def response_breakdown(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> MetricsResponseBreakdown:
    del current_user
    return await service.response_breakdown(_window(service, campaign_id, from_date, to_date))


@metrics_router.get(
    "/decline-reasons",
    response_model=DeclineReasonMetrics,
    summary="Get decline reasons",
)
async def decline_reasons(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> DeclineReasonMetrics:
    del current_user
    return await service.decline_reasons(_window(service, campaign_id, from_date, to_date))


@metrics_router.get("/campaigns", response_model=CampaignMetrics, summary="Compare campaigns")
async def campaign_metrics(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> CampaignMetrics:
    del current_user
    return await service.campaigns(_window(service, campaign_id, from_date, to_date))


@reports_router.get(
    "/inactive-numbers",
    response_model=InactiveNumberPage,
    summary="List inactive numbers",
)
async def inactive_numbers(
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> InactiveNumberPage:
    del current_user
    return await service.inactive_numbers(
        _window(service, campaign_id, from_date, to_date), page=page, page_size=page_size
    )


@reports_router.get("/{report}/export", summary="Export a metrics report")
async def export_report(
    report: ReportName,
    current_user: Annotated[UserOut, Depends(staff_access)],
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    campaign_id: UUID | None = None,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> Response:
    """Download one documented report using the active filters."""
    del current_user
    content = await service.export_csv(report, _window(service, campaign_id, from_date, to_date))
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="tihbc-{report}.csv"'},
    )
