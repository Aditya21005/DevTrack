from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.access_control import is_active_membership
from devtrack_ai_db.models import User

from .repositories import DashboardRepository
from .schemas import (
    ChartPoint,
    DashboardCard,
    DashboardCardsResponse,
    DashboardFilters,
    DashboardOverviewResponse,
    MonthlyStatistic,
    MonthlyStatisticsResponse,
    PendingCompletedResponse,
    PriorityChartResponse,
    ProductivityResponse,
    StatusChartResponse,
    ThroughputChartResponse,
    TimeSeriesPoint,
)


class DashboardError(RuntimeError):
    """Base dashboard domain error."""


class DashboardNotFoundError(DashboardError):
    """Raised when workspace/project context is unavailable."""


class DashboardPermissionError(DashboardError):
    """Raised when the actor cannot view analytics."""


class DashboardValidationError(DashboardError):
    """Raised when analytics filters are invalid."""


DashboardRepositoryFactory = Callable[[AsyncSession], DashboardRepository]


class DashboardService:
    def __init__(self, repository_factory: DashboardRepositoryFactory = DashboardRepository) -> None:
        self.repository_factory = repository_factory

    async def get_cards(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> DashboardCardsResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        period = repository.make_period(filters.start_date, filters.end_date)  # type: ignore[arg-type]
        previous_period = repository.make_period(
            filters.start_date - (filters.end_date - filters.start_date + timedelta(days=1)),  # type: ignore[operator]
            filters.start_date - timedelta(days=1),  # type: ignore[operator]
        )
        counts = await repository.task_counts(workspace_id, filters.project_id)
        current = await repository.task_counts_in_range(workspace_id, period, filters.project_id)
        previous = await repository.task_counts_in_range(workspace_id, previous_period, filters.project_id)
        cards = [
            self._card("total", "Total Tasks", counts["total"]),
            self._card("pending", "Pending", counts["pending"]),
            self._card("completed", "Completed", counts["completed"]),
            self._card("overdue", "Overdue", counts["overdue"]),
            self._card("created_period", "Created", current["created"], previous["created"]),
            self._card("completed_period", "Completed In Period", current["completed"], previous["completed"]),
        ]
        return DashboardCardsResponse(
            workspace_id=workspace_id,
            project_id=filters.project_id,
            start_date=filters.start_date,  # type: ignore[arg-type]
            end_date=filters.end_date,  # type: ignore[arg-type]
            cards=cards,
        )

    async def get_status_chart(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> StatusChartResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        rows = await repository.status_distribution(workspace_id, filters.project_id)
        return StatusChartResponse(workspace_id=workspace_id, project_id=filters.project_id, points=[ChartPoint(label=label, value=value) for label, value in rows])

    async def get_priority_chart(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> PriorityChartResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        rows = await repository.priority_distribution(workspace_id, filters.project_id)
        return PriorityChartResponse(workspace_id=workspace_id, project_id=filters.project_id, points=[ChartPoint(label=label, value=value) for label, value in rows])

    async def get_throughput_chart(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> ThroughputChartResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        period = repository.make_period(filters.start_date, filters.end_date)  # type: ignore[arg-type]
        created = dict(await repository.daily_created_series(workspace_id, period, filters.project_id))
        completed = dict(await repository.daily_completed_series(workspace_id, period, filters.project_id))
        days = self._days(filters.start_date, filters.end_date)  # type: ignore[arg-type]
        return ThroughputChartResponse(
            workspace_id=workspace_id,
            project_id=filters.project_id,
            start_date=filters.start_date,  # type: ignore[arg-type]
            end_date=filters.end_date,  # type: ignore[arg-type]
            created=[TimeSeriesPoint(period=day, value=created.get(day, 0)) for day in days],
            completed=[TimeSeriesPoint(period=day, value=completed.get(day, 0)) for day in days],
        )

    async def get_productivity(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> ProductivityResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        period = repository.make_period(filters.start_date, filters.end_date)  # type: ignore[arg-type]
        counts = await repository.productivity_counts(workspace_id, period, filters.project_id)
        denominator = counts["created_tasks"] or counts["pending_tasks"] + counts["completed_tasks"]
        completion_rate = round((counts["completed_tasks"] / denominator) * 100, 2) if denominator else 0.0
        return ProductivityResponse(
            workspace_id=workspace_id,
            project_id=filters.project_id,
            start_date=filters.start_date,  # type: ignore[arg-type]
            end_date=filters.end_date,  # type: ignore[arg-type]
            completion_rate=completion_rate,
            **counts,
        )

    async def get_pending_completed(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> PendingCompletedResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        counts = await repository.task_counts(workspace_id, filters.project_id)
        return PendingCompletedResponse(workspace_id=workspace_id, project_id=filters.project_id, pending=counts["pending"], completed=counts["completed"], total=counts["total"])

    async def get_monthly_statistics(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> MonthlyStatisticsResponse:
        repository = self.repository_factory(session)
        filters = self._normalize_filters(filters, default_days=365)
        await self._require_access(repository, workspace_id, filters.project_id, actor.id)
        period = repository.make_period(filters.start_date, filters.end_date)  # type: ignore[arg-type]
        rows = await repository.monthly_statistics(workspace_id, period, filters.project_id)
        return MonthlyStatisticsResponse(
            workspace_id=workspace_id,
            project_id=filters.project_id,
            months=[MonthlyStatistic(**row) for row in rows],
        )

    async def get_overview(self, session: AsyncSession, workspace_id: uuid.UUID, filters: DashboardFilters, actor: User) -> DashboardOverviewResponse:
        repository = self.repository_factory(session)
        normalized_filters = self._normalize_filters(filters)
        monthly_filters = self._normalize_filters(filters, default_days=365)
        await self._require_access(repository, workspace_id, normalized_filters.project_id, actor.id)

        period = repository.make_period(normalized_filters.start_date, normalized_filters.end_date)  # type: ignore[arg-type]
        previous_period = repository.make_period(
            normalized_filters.start_date - (normalized_filters.end_date - normalized_filters.start_date + timedelta(days=1)),  # type: ignore[operator]
            normalized_filters.start_date - timedelta(days=1),  # type: ignore[operator]
        )
        monthly_period = repository.make_period(monthly_filters.start_date, monthly_filters.end_date)  # type: ignore[arg-type]

        counts = await repository.task_counts(workspace_id, normalized_filters.project_id)
        current = await repository.task_counts_in_range(workspace_id, period, normalized_filters.project_id)
        previous = await repository.task_counts_in_range(workspace_id, previous_period, normalized_filters.project_id)
        status_rows = await repository.status_distribution(workspace_id, normalized_filters.project_id)
        priority_rows = await repository.priority_distribution(workspace_id, normalized_filters.project_id)
        created_series = dict(await repository.daily_created_series(workspace_id, period, normalized_filters.project_id))
        completed_series = dict(await repository.daily_completed_series(workspace_id, period, normalized_filters.project_id))
        productivity_counts = await repository.productivity_counts_from_precomputed(
            workspace_id,
            period,
            counts=counts,
            range_counts=current,
            project_id=normalized_filters.project_id,
        )
        monthly_rows = await repository.monthly_statistics_from_counts(
            workspace_id,
            monthly_period,
            pending_count=counts["pending"],
            project_id=monthly_filters.project_id,
        )

        cards = DashboardCardsResponse(
            workspace_id=workspace_id,
            project_id=normalized_filters.project_id,
            start_date=normalized_filters.start_date,  # type: ignore[arg-type]
            end_date=normalized_filters.end_date,  # type: ignore[arg-type]
            cards=[
                self._card("total", "Total Tasks", counts["total"]),
                self._card("pending", "Pending", counts["pending"]),
                self._card("completed", "Completed", counts["completed"]),
                self._card("overdue", "Overdue", counts["overdue"]),
                self._card("created_period", "Created", current["created"], previous["created"]),
                self._card("completed_period", "Completed In Period", current["completed"], previous["completed"]),
            ],
        )
        days = self._days(normalized_filters.start_date, normalized_filters.end_date)  # type: ignore[arg-type]
        denominator = productivity_counts["created_tasks"] or productivity_counts["pending_tasks"] + productivity_counts["completed_tasks"]
        completion_rate = round((productivity_counts["completed_tasks"] / denominator) * 100, 2) if denominator else 0.0

        return DashboardOverviewResponse(
            cards=cards,
            status_chart=StatusChartResponse(
                workspace_id=workspace_id,
                project_id=normalized_filters.project_id,
                points=[ChartPoint(label=label, value=value) for label, value in status_rows],
            ),
            priority_chart=PriorityChartResponse(
                workspace_id=workspace_id,
                project_id=normalized_filters.project_id,
                points=[ChartPoint(label=label, value=value) for label, value in priority_rows],
            ),
            throughput_chart=ThroughputChartResponse(
                workspace_id=workspace_id,
                project_id=normalized_filters.project_id,
                start_date=normalized_filters.start_date,  # type: ignore[arg-type]
                end_date=normalized_filters.end_date,  # type: ignore[arg-type]
                created=[TimeSeriesPoint(period=day, value=created_series.get(day, 0)) for day in days],
                completed=[TimeSeriesPoint(period=day, value=completed_series.get(day, 0)) for day in days],
            ),
            productivity=ProductivityResponse(
                workspace_id=workspace_id,
                project_id=normalized_filters.project_id,
                start_date=normalized_filters.start_date,  # type: ignore[arg-type]
                end_date=normalized_filters.end_date,  # type: ignore[arg-type]
                completion_rate=completion_rate,
                **productivity_counts,
            ),
            pending_completed=PendingCompletedResponse(
                workspace_id=workspace_id,
                project_id=normalized_filters.project_id,
                pending=counts["pending"],
                completed=counts["completed"],
                total=counts["total"],
            ),
            monthly_statistics=MonthlyStatisticsResponse(
                workspace_id=workspace_id,
                project_id=monthly_filters.project_id,
                months=[MonthlyStatistic(**row) for row in monthly_rows],
            ),
        )

    async def _require_access(self, repository: DashboardRepository, workspace_id: uuid.UUID, project_id: uuid.UUID | None, actor_id: uuid.UUID) -> None:
        if await repository.get_workspace(workspace_id) is None:
            raise DashboardNotFoundError("Workspace not found")
        if project_id is not None and await repository.get_project(workspace_id, project_id) is None:
            raise DashboardNotFoundError("Project not found")
        membership_and_role = await repository.get_membership(workspace_id, actor_id)
        if membership_and_role is None:
            raise DashboardPermissionError("Workspace membership required")
        membership, _role = membership_and_role
        if not is_active_membership(membership):
            raise DashboardPermissionError("Active workspace membership required")

    def _normalize_filters(self, filters: DashboardFilters, default_days: int = 30) -> DashboardFilters:
        today = date.today()
        start_date = filters.start_date or today - timedelta(days=default_days)
        end_date = filters.end_date or today
        if start_date > end_date:
            raise DashboardValidationError("start_date cannot be after end_date")
        if (end_date - start_date).days > 730:
            raise DashboardValidationError("Dashboard date range cannot exceed 730 days")
        return DashboardFilters(project_id=filters.project_id, start_date=start_date, end_date=end_date)

    def _card(self, key: str, label: str, value: int | float, previous_value: int | float | None = None) -> DashboardCard:
        delta = value - previous_value if previous_value is not None else None
        return DashboardCard(key=key, label=label, value=value, previous_value=previous_value, delta=delta)

    def _days(self, start_date: date, end_date: date) -> list[date]:
        count = (end_date - start_date).days + 1
        return [start_date + timedelta(days=offset) for offset in range(count)]


def get_dashboard_service() -> DashboardService:
    return DashboardService()
