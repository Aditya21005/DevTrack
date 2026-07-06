from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.models import Board, BoardColumn, Issue, IssueAssignee, IssueType, Membership, Organization, Project, Role, User

from .models import KanbanEvent, KanbanEventType


@dataclass(frozen=True)
class BoardContext:
    board: Board
    project: Project


class KanbanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_workspace(self, workspace_id: uuid.UUID) -> Organization | None:
        workspace = await self.session.get(Organization, workspace_id)
        if workspace is None or workspace.deleted_at is not None:
            return None
        return workspace

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

    async def get_board_context(self, workspace_id: uuid.UUID, board_id: uuid.UUID) -> BoardContext | None:
        result = await self.session.execute(
            select(Board, Project)
            .join(Project, Board.project_id == Project.id)
            .where(
                Board.id == board_id,
                Board.organization_id == workspace_id,
                Board.deleted_at.is_(None),
                Project.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        board, project = row
        return BoardContext(board=board, project=project)

    async def get_columns(self, workspace_id: uuid.UUID, board_id: uuid.UUID) -> list[BoardColumn]:
        result = await self.session.execute(
            select(BoardColumn)
            .where(
                BoardColumn.organization_id == workspace_id,
                BoardColumn.board_id == board_id,
                BoardColumn.deleted_at.is_(None),
            )
            .order_by(BoardColumn.position.asc())
        )
        return list(result.scalars().all())

    async def get_column(self, workspace_id: uuid.UUID, board_id: uuid.UUID, column_id: uuid.UUID) -> BoardColumn | None:
        column = await self.session.get(BoardColumn, column_id)
        if column is None or column.deleted_at is not None:
            return None
        if column.organization_id != workspace_id or column.board_id != board_id:
            return None
        return column

    async def get_task_for_update(self, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID) -> Issue | None:
        result = await self.session.execute(
            select(Issue)
            .where(
                Issue.id == task_id,
                Issue.organization_id == workspace_id,
                Issue.project_id == project_id,
                Issue.issue_type == IssueType.task,
                Issue.deleted_at.is_(None),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_task(self, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID) -> Issue | None:
        result = await self.session.execute(
            select(Issue).where(
                Issue.id == task_id,
                Issue.organization_id == workspace_id,
                Issue.project_id == project_id,
                Issue.issue_type == IssueType.task,
                Issue.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_column_tasks(self, workspace_id: uuid.UUID, project_id: uuid.UUID, status_id: uuid.UUID) -> list[Issue]:
        result = await self.session.execute(
            select(Issue)
            .where(
                Issue.organization_id == workspace_id,
                Issue.project_id == project_id,
                Issue.status_id == status_id,
                Issue.issue_type == IssueType.task,
                Issue.deleted_at.is_(None),
            )
            .order_by(Issue.rank.asc(), Issue.issue_number.asc())
        )
        return list(result.scalars().all())

    async def count_column_tasks(self, workspace_id: uuid.UUID, project_id: uuid.UUID, status_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(Issue.id)).where(
                Issue.organization_id == workspace_id,
                Issue.project_id == project_id,
                Issue.status_id == status_id,
                Issue.issue_type == IssueType.task,
                Issue.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def list_assignee_ids(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.session.execute(
            select(IssueAssignee.user_id).where(
                IssueAssignee.organization_id == workspace_id,
                IssueAssignee.issue_id == task_id,
                IssueAssignee.deleted_at.is_(None),
            )
        )
        return [user_id for user_id in result.scalars().all()]

    async def save_event(
        self,
        *,
        workspace_id: uuid.UUID,
        board_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        actor_id: uuid.UUID,
        event_type: KanbanEventType,
        event_key: str,
        payload: dict,
    ) -> KanbanEvent:
        event = KanbanEvent(
            organization_id=workspace_id,
            board_id=board_id,
            project_id=project_id,
            task_id=task_id,
            actor_id=actor_id,
            event_type=event_type,
            event_key=event_key,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return event
