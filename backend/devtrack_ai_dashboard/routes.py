from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_auth.routes import CurrentUser
from devtrack_ai_db.session import get_db_session

from .schemas import (
    DashboardCardsResponse,
    DashboardFilters,
    DashboardOverviewResponse,
    MonthlyStatisticsResponse,
    PendingCompletedResponse,
    PriorityChartResponse,
    ProductivityResponse,
    StatusChartResponse,
    ThroughputChartResponse,
)
from .services import (
    DashboardError,
    DashboardNotFoundError,
    DashboardPermissionError,
    DashboardService,
    DashboardValidationError,
    get_dashboard_service,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/dashboard", tags=["dashboard"])

ReadOnlyDbSession = Annotated[AsyncSession, Depends(get_db_session)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


def dashboard_filters(
    project_id: uuid.UUID | None = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> DashboardFilters:
    return DashboardFilters(project_id=project_id, start_date=start_date, end_date=end_date)


def map_dashboard_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DashboardNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, DashboardPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, DashboardValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, DashboardError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard analytics failed")


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> DashboardOverviewResponse:
    try:
        return await dashboard_service.get_overview(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/cards", response_model=DashboardCardsResponse)
async def get_dashboard_cards(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> DashboardCardsResponse:
    try:
        return await dashboard_service.get_cards(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/charts/status", response_model=StatusChartResponse)
async def get_status_chart(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> StatusChartResponse:
    try:
        return await dashboard_service.get_status_chart(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/charts/priority", response_model=PriorityChartResponse)
async def get_priority_chart(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> PriorityChartResponse:
    try:
        return await dashboard_service.get_priority_chart(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/charts/throughput", response_model=ThroughputChartResponse)
async def get_throughput_chart(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> ThroughputChartResponse:
    try:
        return await dashboard_service.get_throughput_chart(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/productivity", response_model=ProductivityResponse)
async def get_productivity(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> ProductivityResponse:
    try:
        return await dashboard_service.get_productivity(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/pending-completed", response_model=PendingCompletedResponse)
async def get_pending_completed(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> PendingCompletedResponse:
    try:
        return await dashboard_service.get_pending_completed(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc


@router.get("/monthly-statistics", response_model=MonthlyStatisticsResponse)
async def get_monthly_statistics(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    dashboard_service: DashboardServiceDep,
    filters: Annotated[DashboardFilters, Depends(dashboard_filters)],
) -> MonthlyStatisticsResponse:
    try:
        return await dashboard_service.get_monthly_statistics(session, workspace_id, filters, current_user)
    except Exception as exc:
        raise map_dashboard_error(exc) from exc
