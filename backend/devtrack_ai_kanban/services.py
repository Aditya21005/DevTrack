from __future__ import annotations

import logging
import uuid
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.access_control import is_active_membership
from devtrack_ai_db.models import BoardColumn, Issue, User

from .models import KanbanEventType
from .repositories import BoardContext, KanbanRepository
from .schemas import KanbanBoardResponse, KanbanColumnResponse, KanbanMutationResponse, KanbanTaskCard, MoveTaskRequest, UpdateTaskStatusRequest

logger = logging.getLogger(__name__)

RANK_STEP = 1024
RANK_WIDTH = 20


class KanbanError(RuntimeError):
    """Base Kanban domain error."""


class KanbanNotFoundError(KanbanError):
    """Raised when board, column, or task data cannot be found."""


class KanbanPermissionError(KanbanError):
    """Raised when the actor cannot access the board."""


class KanbanConflictError(KanbanError):
    """Raised when a drag/drop mutation conflicts with board state."""


class KanbanValidationError(KanbanError):
    """Raised when a Kanban operation violates business rules."""


KanbanRepositoryFactory = Callable[[AsyncSession], KanbanRepository]


class KanbanService:
    def __init__(self, repository_factory: KanbanRepositoryFactory = KanbanRepository) -> None:
        self.repository_factory = repository_factory

    async def get_board(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        board_id: uuid.UUID,
        actor: User,
    ) -> KanbanBoardResponse:
        repository = self.repository_factory(session)
        context = await self._get_board_context_required(repository, workspace_id, board_id)
        await self._require_member(repository, workspace_id, actor.id)
        return await self._build_board_response(repository, context)

    async def move_task(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        board_id: uuid.UUID,
        payload: MoveTaskRequest,
        actor: User,
        event_type: KanbanEventType = KanbanEventType.task_moved,
    ) -> KanbanMutationResponse:
        repository = self.repository_factory(session)
        context = await self._get_board_context_required(repository, workspace_id, board_id)
        await self._require_member(repository, workspace_id, actor.id)
        target_column = await self._get_column_required(repository, workspace_id, board_id, payload.target_column_id)
        task = await self._get_task_for_update_required(repository, workspace_id, context.project.id, payload.task_id)

        await self._ensure_wip_allows_move(repository, workspace_id, context.project.id, target_column, task)
        target_tasks = await repository.get_column_tasks(workspace_id, context.project.id, target_column.workflow_status_id)
        target_tasks = [candidate for candidate in target_tasks if candidate.id != task.id]
        insert_index = self._resolve_insert_index(target_tasks, payload.before_task_id, payload.after_task_id)
        new_rank = self._rank_for_insert(target_tasks, insert_index, actor.id)

        old_status_id = task.status_id
        old_rank = task.rank
        task.status_id = target_column.workflow_status_id
        task.rank = new_rank
        task.updated_by_id = actor.id
        task.version += 1
        await session.flush()

        event = await repository.save_event(
            workspace_id=workspace_id,
            board_id=board_id,
            project_id=context.project.id,
            task_id=task.id,
            actor_id=actor.id,
            event_type=event_type,
            event_key=payload.client_event_id or f"{event_type.value}:{task.id}:{task.version}",
            payload={
                "task_id": str(task.id),
                "project_id": str(context.project.id),
                "board_id": str(board_id),
                "from_status_id": str(old_status_id),
                "to_status_id": str(task.status_id),
                "from_rank": old_rank,
                "to_rank": task.rank,
                "before_task_id": str(payload.before_task_id) if payload.before_task_id else None,
                "after_task_id": str(payload.after_task_id) if payload.after_task_id else None,
            },
        )

        logger.info("kanban.task_moved", extra={"board_id": str(board_id), "task_id": str(task.id), "actor_id": str(actor.id), "event_type": event_type.value})
        card = await self._task_card_for_single_task(repository, workspace_id, task)
        return KanbanMutationResponse(task=card, event_id=event.id, event_type=event.event_type, board_version=task.version)

    async def update_status(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        board_id: uuid.UUID,
        payload: UpdateTaskStatusRequest,
        actor: User,
    ) -> KanbanMutationResponse:
        move_payload = MoveTaskRequest(
            task_id=payload.task_id,
            target_column_id=payload.target_column_id,
            client_event_id=payload.client_event_id,
        )
        return await self.move_task(
            session,
            workspace_id,
            board_id,
            move_payload,
            actor,
            event_type=KanbanEventType.task_status_updated,
        )

    async def _build_board_response(self, repository: KanbanRepository, context: BoardContext) -> KanbanBoardResponse:
        columns = await repository.get_columns(context.board.organization_id, context.board.id)
        status_ids = [column.workflow_status_id for column in columns]
        tasks_by_status = await repository.get_tasks_by_status(context.board.organization_id, context.project.id, status_ids)
        task_ids = [task.id for tasks in tasks_by_status.values() for task in tasks]
        assignee_ids_by_task = await repository.list_assignee_ids_for_tasks(context.board.organization_id, task_ids)

        column_responses: list[KanbanColumnResponse] = []
        for column in columns:
            tasks = tasks_by_status.get(column.workflow_status_id, [])
            cards = [self._task_card(task, assignee_ids_by_task.get(task.id, [])) for task in tasks]
            column_responses.append(
                KanbanColumnResponse(
                    id=column.id,
                    name=column.name,
                    workflow_status_id=column.workflow_status_id,
                    position=column.position,
                    wip_limit=column.wip_limit,
                    tasks=cards,
                )
            )
        return KanbanBoardResponse(
            id=context.board.id,
            organization_id=context.board.organization_id,
            project_id=context.project.id,
            name=context.board.name,
            is_default=context.board.is_default,
            columns=column_responses,
        )

    async def _task_card_for_single_task(self, repository: KanbanRepository, workspace_id: uuid.UUID, task: Issue) -> KanbanTaskCard:
        assignee_ids = await repository.list_assignee_ids(workspace_id, task.id)
        return self._task_card(task, assignee_ids)

    def _task_card(self, task: Issue, assignee_ids: list[uuid.UUID]) -> KanbanTaskCard:
        return KanbanTaskCard(
            id=task.id,
            issue_number=task.issue_number,
            title=task.title,
            priority=task.priority.value,
            rank=task.rank,
            status_id=task.status_id,
            assignee_ids=assignee_ids,
            due_at=task.due_at,
            updated_at=task.updated_at,
        )

    async def _get_board_context_required(self, repository: KanbanRepository, workspace_id: uuid.UUID, board_id: uuid.UUID) -> BoardContext:
        context = await repository.get_board_context(workspace_id, board_id)
        if context is None:
            raise KanbanNotFoundError("Board not found")
        return context

    async def _get_column_required(self, repository: KanbanRepository, workspace_id: uuid.UUID, board_id: uuid.UUID, column_id: uuid.UUID) -> BoardColumn:
        column = await repository.get_column(workspace_id, board_id, column_id)
        if column is None:
            raise KanbanNotFoundError("Board column not found")
        return column

    async def _get_task_for_update_required(self, repository: KanbanRepository, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID) -> Issue:
        task = await repository.get_task_for_update(workspace_id, project_id, task_id)
        if task is None:
            raise KanbanNotFoundError("Task not found")
        return task

    async def _require_member(self, repository: KanbanRepository, workspace_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        if await repository.get_workspace(workspace_id) is None:
            raise KanbanNotFoundError("Workspace not found")
        membership_and_role = await repository.get_membership(workspace_id, actor_id)
        if membership_and_role is None:
            raise KanbanPermissionError("Workspace membership required")
        membership, _role = membership_and_role
        if not is_active_membership(membership):
            raise KanbanPermissionError("Active workspace membership required")

    async def _ensure_wip_allows_move(
        self,
        repository: KanbanRepository,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        target_column: BoardColumn,
        task: Issue,
    ) -> None:
        if target_column.wip_limit is None:
            return
        if task.status_id == target_column.workflow_status_id:
            return
        count = await repository.count_column_tasks(workspace_id, project_id, target_column.workflow_status_id)
        if count >= target_column.wip_limit:
            raise KanbanConflictError("Target column WIP limit has been reached")

    def _resolve_insert_index(
        self,
        target_tasks: list[Issue],
        before_task_id: uuid.UUID | None,
        after_task_id: uuid.UUID | None,
    ) -> int:
        task_ids = [task.id for task in target_tasks]
        if before_task_id is not None and before_task_id not in task_ids:
            raise KanbanValidationError("before_task_id must belong to the target column")
        if after_task_id is not None and after_task_id not in task_ids:
            raise KanbanValidationError("after_task_id must belong to the target column")
        if before_task_id is None and after_task_id is None:
            return len(target_tasks)
        if before_task_id is not None and after_task_id is None:
            return task_ids.index(before_task_id)
        if after_task_id is not None and before_task_id is None:
            return task_ids.index(after_task_id) + 1

        before_index = task_ids.index(before_task_id)  # type: ignore[arg-type]
        after_index = task_ids.index(after_task_id)  # type: ignore[arg-type]
        if after_index + 1 != before_index:
            raise KanbanValidationError("before_task_id must immediately follow after_task_id")
        return before_index

    def _rank_for_insert(self, target_tasks: list[Issue], insert_index: int, actor_id: uuid.UUID) -> str:
        values = [self._rank_value(task.rank, index) for index, task in enumerate(target_tasks)]
        previous_value = values[insert_index - 1] if insert_index > 0 else None
        next_value = values[insert_index] if insert_index < len(values) else None

        if previous_value is None and next_value is None:
            return self._format_rank(RANK_STEP)
        if previous_value is None:
            if next_value and next_value > 1:
                return self._format_rank(next_value // 2)
            return self._compact_and_rank(target_tasks, insert_index, actor_id)
        if next_value is None:
            return self._format_rank(previous_value + RANK_STEP)
        if next_value - previous_value > 1:
            return self._format_rank((previous_value + next_value) // 2)
        return self._compact_and_rank(target_tasks, insert_index, actor_id)

    def _compact_and_rank(self, target_tasks: list[Issue], insert_index: int, actor_id: uuid.UUID) -> str:
        new_rank: str | None = None
        output_position = 0
        for input_position, task in enumerate(target_tasks):
            if output_position == insert_index:
                new_rank = self._format_rank((output_position + 1) * RANK_STEP)
                output_position += 1
            task.rank = self._format_rank((output_position + 1) * RANK_STEP)
            task.updated_by_id = actor_id
            task.version += 1
            output_position += 1
        if new_rank is None:
            new_rank = self._format_rank((output_position + 1) * RANK_STEP)
        return new_rank

    def _rank_value(self, rank: str, index: int) -> int:
        if rank.isdigit():
            return int(rank)
        return (index + 1) * RANK_STEP

    def _format_rank(self, value: int) -> str:
        return str(value).zfill(RANK_WIDTH)


def get_kanban_service() -> KanbanService:
    return KanbanService()
