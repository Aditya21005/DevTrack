from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.models import ActivityEvent, Comment, Issue, IssueType, Membership, Organization, Project, Role, StatusCategory, WorkflowStatus


@dataclass(frozen=True)
class DateRange:
    start: datetime
    end: datetime


class DashboardRepository:
    """Read-optimized aggregate queries for dashboard analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_workspace(self, workspace_id: uuid.UUID) -> Organization | None:
        workspace = await self.session.get(Organization, workspace_id)
        if workspace is None or workspace.deleted_at is not None:
            return None
        return workspace

    async def get_project(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project | None:
        project = await self.session.get(Project, project_id)
        if project is None or project.deleted_at is not None or project.organization_id != workspace_id:
            return None
        return project

    async def get_membership(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> tuple[Membership, Role | None] | None:
        result = await self.session.execute(
            select(Membership, Role)
            .outerjoin(Role, Membership.role_id == Role.id)
            .where(
                Membership.organization_id == workspace_id,
                Membership.user_id == user_id,
                Membership.deleted_at.is_(None),
            )
        )
        return result.one_or_none()

    async def task_counts(self, workspace_id: uuid.UUID, project_id: uuid.UUID | None = None) -> dict[str, int]:
        query = (
            select(
                func.count(Issue.id).label("total"),
                func.sum(case((WorkflowStatus.category == StatusCategory.done, 1), else_=0)).label("completed"),
                func.sum(case((WorkflowStatus.category.in_([StatusCategory.todo, StatusCategory.in_progress]), 1), else_=0)).label("pending"),
                func.sum(case((WorkflowStatus.category == StatusCategory.canceled, 1), else_=0)).label("canceled"),
                func.sum(case((Issue.due_at < func.now(), 1), else_=0)).label("overdue"),
            )
            .join(WorkflowStatus, Issue.status_id == WorkflowStatus.id)
            .where(*self._task_scope(workspace_id, project_id))
        )
        row = (await self.session.execute(query)).one()
        return {key: int(getattr(row, key) or 0) for key in ["total", "completed", "pending", "canceled", "overdue"]}

    async def task_counts_in_range(self, workspace_id: uuid.UUID, period: DateRange, project_id: uuid.UUID | None = None) -> dict[str, int]:
        query = (
            select(
                func.sum(case((Issue.created_at >= period.start, case((Issue.created_at < period.end, 1), else_=0)), else_=0)).label("created"),
                func.sum(
                    case(
                        (
                            WorkflowStatus.category == StatusCategory.done,
                            case((Issue.updated_at >= period.start, case((Issue.updated_at < period.end, 1), else_=0)), else_=0),
                        ),
                        else_=0,
                    )
                ).label("completed"),
            )
            .join(WorkflowStatus, Issue.status_id == WorkflowStatus.id)
            .where(*self._task_scope(workspace_id, project_id))
        )
        row = (await self.session.execute(query)).one()
        return {"created": int(row.created or 0), "completed": int(row.completed or 0)}

    async def status_distribution(self, workspace_id: uuid.UUID, project_id: uuid.UUID | None = None) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(WorkflowStatus.category, func.count(Issue.id))
            .join(WorkflowStatus, Issue.status_id == WorkflowStatus.id)
            .where(*self._task_scope(workspace_id, project_id))
            .group_by(WorkflowStatus.category)
            .order_by(WorkflowStatus.category.asc())
        )
        return [(category.value, int(count)) for category, count in result.all()]

    async def priority_distribution(self, workspace_id: uuid.UUID, project_id: uuid.UUID | None = None) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(Issue.priority, func.count(Issue.id))
            .where(*self._task_scope(workspace_id, project_id))
            .group_by(Issue.priority)
            .order_by(Issue.priority.asc())
        )
        return [(priority.value, int(count)) for priority, count in result.all()]

    async def daily_created_series(self, workspace_id: uuid.UUID, period: DateRange, project_id: uuid.UUID | None = None) -> list[tuple[date, int]]:
        day_expr = func.date_trunc("day", Issue.created_at).label("day")
        result = await self.session.execute(
            select(day_expr, func.count(Issue.id))
            .where(*self._task_scope(workspace_id, project_id), Issue.created_at >= period.start, Issue.created_at < period.end)
            .group_by(day_expr)
            .order_by(day_expr.asc())
        )
        return [(self._as_date(day), int(count)) for day, count in result.all()]

    async def daily_completed_series(self, workspace_id: uuid.UUID, period: DateRange, project_id: uuid.UUID | None = None) -> list[tuple[date, int]]:
        day_expr = func.date_trunc("day", Issue.updated_at).label("day")
        result = await self.session.execute(
            select(day_expr, func.count(Issue.id))
            .join(WorkflowStatus, Issue.status_id == WorkflowStatus.id)
            .where(
                *self._task_scope(workspace_id, project_id),
                WorkflowStatus.category == StatusCategory.done,
                Issue.updated_at >= period.start,
                Issue.updated_at < period.end,
            )
            .group_by(day_expr)
            .order_by(day_expr.asc())
        )
        return [(self._as_date(day), int(count)) for day, count in result.all()]

    async def productivity_counts(self, workspace_id: uuid.UUID, period: DateRange, project_id: uuid.UUID | None = None) -> dict[str, int]:
        task_counts = await self.task_counts(workspace_id, project_id)
        range_counts = await self.task_counts_in_range(workspace_id, period, project_id)
        return await self.productivity_counts_from_precomputed(
            workspace_id,
            period,
            counts=task_counts,
            range_counts=range_counts,
            project_id=project_id,
        )

    async def productivity_counts_from_precomputed(
        self,
        workspace_id: uuid.UUID,
        period: DateRange,
        *,
        counts: dict[str, int],
        range_counts: dict[str, int],
        project_id: uuid.UUID | None = None,
    ) -> dict[str, int]:
        comment_filters = [
            Comment.organization_id == workspace_id,
            Comment.deleted_at.is_(None),
            Comment.created_at >= period.start,
            Comment.created_at < period.end,
        ]
        if project_id is not None:
            comment_filters.extend(
                [
                    Issue.id == Comment.issue_id,
                    Issue.project_id == project_id,
                    Issue.deleted_at.is_(None),
                ]
            )
        comments_query = select(func.count(Comment.id)).where(*comment_filters)
        events_query = (
            select(func.count(ActivityEvent.id))
            .where(
                ActivityEvent.organization_id == workspace_id,
                ActivityEvent.created_at >= period.start,
                ActivityEvent.created_at < period.end,
            )
        )
        comments = int((await self.session.execute(comments_query)).scalar_one() or 0)
        events = int((await self.session.execute(events_query)).scalar_one() or 0)
        return {
            "created_tasks": range_counts["created"],
            "completed_tasks": range_counts["completed"],
            "pending_tasks": counts["pending"],
            "overdue_tasks": counts["overdue"],
            "comments_added": comments,
            "activity_events": events,
        }

    async def monthly_statistics(self, workspace_id: uuid.UUID, period: DateRange, project_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
        pending_snapshot = await self.task_counts(workspace_id, project_id)
        return await self.monthly_statistics_from_counts(
            workspace_id,
            period,
            pending_count=pending_snapshot["pending"],
            project_id=project_id,
        )

    async def monthly_statistics_from_counts(
        self,
        workspace_id: uuid.UUID,
        period: DateRange,
        *,
        pending_count: int,
        project_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        created_month = func.date_trunc("month", Issue.created_at).label("month")
        completed_month = func.date_trunc("month", Issue.updated_at).label("month")
        created_rows = await self.session.execute(
            select(created_month, func.count(Issue.id))
            .where(*self._task_scope(workspace_id, project_id), Issue.created_at >= period.start, Issue.created_at < period.end)
            .group_by(created_month)
        )
        completed_rows = await self.session.execute(
            select(completed_month, func.count(Issue.id))
            .join(WorkflowStatus, Issue.status_id == WorkflowStatus.id)
            .where(
                *self._task_scope(workspace_id, project_id),
                WorkflowStatus.category == StatusCategory.done,
                Issue.updated_at >= period.start,
                Issue.updated_at < period.end,
            )
            .group_by(completed_month)
        )
        by_month: dict[date, dict[str, Any]] = {}
        for month, count in created_rows.all():
            key = self._as_date(month).replace(day=1)
            by_month.setdefault(key, {"month": key, "created": 0, "completed": 0, "pending_snapshot": 0})["created"] = int(count)
        for month, count in completed_rows.all():
            key = self._as_date(month).replace(day=1)
            by_month.setdefault(key, {"month": key, "created": 0, "completed": 0, "pending_snapshot": 0})["completed"] = int(count)
        for value in by_month.values():
            value["pending_snapshot"] = pending_count
        return [by_month[key] for key in sorted(by_month)]

    def make_period(self, start_date: date, end_date: date) -> DateRange:
        return DateRange(
            start=datetime.combine(start_date, time.min, tzinfo=UTC),
            end=datetime.combine(end_date, time.min, tzinfo=UTC) + timedelta(days=1),
        )

    def _task_scope(self, workspace_id: uuid.UUID, project_id: uuid.UUID | None = None) -> list[Any]:
        filters: list[Any] = [
            Issue.organization_id == workspace_id,
            Issue.issue_type == IssueType.task,
            Issue.deleted_at.is_(None),
        ]
        if project_id is not None:
            filters.append(Issue.project_id == project_id)
        return filters

    def _as_date(self, value: Any) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.fromisoformat(str(value)).date()
