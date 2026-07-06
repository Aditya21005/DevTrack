from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from pydantic import BaseModel, Field, model_validator


class DashboardDateRange(BaseModel):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "DashboardDateRange":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self

    @classmethod
    def default(cls) -> "DashboardDateRange":
        today = date.today()
        return cls(start_date=today - timedelta(days=30), end_date=today)


class DashboardFilters(DashboardDateRange):
    project_id: uuid.UUID | None = None


class DashboardCard(BaseModel):
    key: str
    label: str
    value: int | float
    previous_value: int | float | None = None
    delta: int | float | None = None
    unit: str | None = None


class DashboardCardsResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    cards: list[DashboardCard]


class ChartPoint(BaseModel):
    label: str
    value: int | float


class TimeSeriesPoint(BaseModel):
    period: date
    value: int | float


class StatusChartResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    points: list[ChartPoint]


class PriorityChartResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    points: list[ChartPoint]


class ThroughputChartResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    created: list[TimeSeriesPoint]
    completed: list[TimeSeriesPoint]


class ProductivityResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    created_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float = Field(ge=0)
    comments_added: int
    activity_events: int


class PendingCompletedResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    pending: int
    completed: int
    total: int


class MonthlyStatistic(BaseModel):
    month: date
    created: int
    completed: int
    pending_snapshot: int


class MonthlyStatisticsResponse(BaseModel):
    workspace_id: uuid.UUID
    project_id: uuid.UUID | None = None
    months: list[MonthlyStatistic]


class DashboardOverviewResponse(BaseModel):
    cards: DashboardCardsResponse
    status_chart: StatusChartResponse
    priority_chart: PriorityChartResponse
    throughput_chart: ThroughputChartResponse
    productivity: ProductivityResponse
    pending_completed: PendingCompletedResponse
    monthly_statistics: MonthlyStatisticsResponse
