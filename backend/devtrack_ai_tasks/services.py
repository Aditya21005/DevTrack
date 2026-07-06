from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.access_control import is_active_membership
from devtrack_ai_db.models import (
    Attachment,
    Comment,
    Issue,
    IssueAssignee,
    IssueLabel,
    IssueLink,
    IssueType,
    Label,
    User,
)

from .models import TaskProgress
from .repositories import TaskRecord, TaskRepository
from .schemas import (
    TaskAssignRequest,
    TaskAssigneeResponse,
    TaskAttachmentCreateRequest,
    TaskAttachmentResponse,
    TaskCommentCreateRequest,
    TaskCommentResponse,
    TaskCreateRequest,
    TaskDependencyCreateRequest,
    TaskDependencyResponse,
    TaskLabelAttachRequest,
    TaskLabelCreateRequest,
    TaskLabelResponse,
    TaskPriorityUpdateRequest,
    TaskProgressResponse,
    TaskProgressUpdateRequest,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)

logger = logging.getLogger(__name__)


class TaskError(RuntimeError):
    """Base task domain error."""


class TaskNotFoundError(TaskError):
    """Raised when task-related data cannot be found."""


class TaskConflictError(TaskError):
    """Raised when task data conflicts with existing state."""


class TaskPermissionError(TaskError):
    """Raised when the actor lacks task permissions."""


class TaskValidationError(TaskError):
    """Raised when task data violates business rules."""


TaskRepositoryFactory = Callable[[AsyncSession], TaskRepository]


class TaskService:
    def __init__(self, repository_factory: TaskRepositoryFactory = TaskRepository) -> None:
        self.repository_factory = repository_factory

    async def create_task(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        payload: TaskCreateRequest,
        actor: User,
    ) -> TaskResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._require_status(repository, workspace_id, project_id, payload.status_id)
        if payload.parent_task_id is not None:
            await self._get_task_required(repository, workspace_id, project_id, payload.parent_task_id)

        issue_number = await repository.next_issue_number(project_id)
        now_rank = f"{self._now().timestamp():.6f}-{issue_number}"
        task = Issue(
            organization_id=workspace_id,
            project_id=project_id,
            issue_number=issue_number,
            parent_issue_id=payload.parent_task_id,
            status_id=payload.status_id,
            reporter_id=actor.id,
            title=payload.title,
            description=payload.description,
            issue_type=IssueType.task,
            priority=payload.priority,
            rank=now_rank,
            story_points=Decimal(str(payload.story_points)) if payload.story_points is not None else None,
            due_at=payload.due_at,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        await repository.add_task(task)
        progress = TaskProgress(
            organization_id=workspace_id,
            issue_id=task.id,
            percent_complete=payload.percent_complete,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        await repository.add_progress(progress)

        for user_id in payload.assignee_ids:
            await self._assign_user(repository, workspace_id, task.id, user_id, actor.id)
        for label_id in payload.label_ids:
            await self._attach_label(repository, workspace_id, project_id, task.id, label_id, actor.id)

        logger.info("task.created", extra={"workspace_id": str(workspace_id), "project_id": str(project_id), "task_id": str(task.id)})
        return await self._build_response(repository, TaskRecord(task=task, progress=progress))

    async def list_tasks(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, actor: User) -> list[TaskResponse]:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        records = await repository.list_task_records(workspace_id, project_id)
        return [await self._build_response(repository, record) for record in records]

    async def get_task(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, actor: User) -> TaskResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        record = await self._get_task_required(repository, workspace_id, project_id, task_id)
        return await self._build_response(repository, record)

    async def update_task(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        payload: TaskUpdateRequest,
        actor: User,
    ) -> TaskResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        record = await self._get_task_required(repository, workspace_id, project_id, task_id, for_update=True)
        fields = payload.model_fields_set

        if payload.status_id is not None:
            await self._require_status(repository, workspace_id, project_id, payload.status_id)
            record.task.status_id = payload.status_id
        if payload.parent_task_id is not None:
            if payload.parent_task_id == task_id:
                raise TaskValidationError("Task cannot be its own parent")
            await self._get_task_required(repository, workspace_id, project_id, payload.parent_task_id)
            record.task.parent_issue_id = payload.parent_task_id
        elif "parent_task_id" in fields:
            record.task.parent_issue_id = None
        if payload.title is not None:
            record.task.title = payload.title
        if "description" in fields:
            record.task.description = payload.description
        if payload.priority is not None:
            record.task.priority = payload.priority
        if "due_at" in fields:
            record.task.due_at = payload.due_at
        if "story_points" in fields:
            record.task.story_points = Decimal(str(payload.story_points)) if payload.story_points is not None else None
        if payload.percent_complete is not None:
            record.progress.percent_complete = payload.percent_complete

        record.task.updated_by_id = actor.id
        record.task.version += 1
        record.progress.updated_by_id = actor.id
        record.progress.version += 1
        await session.flush()
        logger.info("task.updated", extra={"task_id": str(task_id), "actor_id": str(actor.id)})
        return await self._build_response(repository, record)

    async def delete_task(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, actor: User) -> None:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        record = await self._get_task_required(repository, workspace_id, project_id, task_id, for_update=True)
        now = self._now()
        record.task.deleted_at = now
        record.task.deleted_by_id = actor.id
        record.task.updated_by_id = actor.id
        record.task.version += 1
        record.progress.deleted_at = now
        record.progress.deleted_by_id = actor.id
        record.progress.updated_by_id = actor.id
        record.progress.version += 1
        await session.flush()
        logger.info("task.deleted", extra={"task_id": str(task_id), "actor_id": str(actor.id)})

    async def assign_task(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskAssignRequest, actor: User) -> TaskResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        record = await self._get_task_required(repository, workspace_id, project_id, task_id)
        await self._assign_user(repository, workspace_id, task_id, payload.user_id, actor.id)
        return await self._build_response(repository, record)

    async def create_label(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, payload: TaskLabelCreateRequest, actor: User) -> TaskLabelResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        if await repository.label_name_exists(workspace_id, project_id, payload.name):
            raise TaskConflictError("Label name is already in use")
        label = Label(
            organization_id=workspace_id,
            project_id=project_id,
            name=payload.name,
            color=payload.color,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        await repository.add_label(label)
        return TaskLabelResponse.model_validate(label)

    async def attach_label(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskLabelAttachRequest, actor: User) -> TaskResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        record = await self._get_task_required(repository, workspace_id, project_id, task_id)
        await self._attach_label(repository, workspace_id, project_id, task_id, payload.label_id, actor.id)
        return await self._build_response(repository, record)

    async def add_comment(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskCommentCreateRequest, actor: User) -> TaskCommentResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._get_task_required(repository, workspace_id, project_id, task_id)
        comment = Comment(
            organization_id=workspace_id,
            issue_id=task_id,
            author_id=actor.id,
            body=payload.body,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        await repository.add_comment(comment)
        return TaskCommentResponse.model_validate(comment)

    async def list_comments(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, actor: User) -> list[TaskCommentResponse]:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._get_task_required(repository, workspace_id, project_id, task_id)
        comments = await repository.list_comments(workspace_id, task_id)
        return [TaskCommentResponse.model_validate(comment) for comment in comments]

    async def add_attachment(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskAttachmentCreateRequest, actor: User) -> TaskAttachmentResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._get_task_required(repository, workspace_id, project_id, task_id)
        if payload.comment_id is not None and await repository.get_comment(workspace_id, task_id, payload.comment_id) is None:
            raise TaskNotFoundError("Comment not found")
        attachment = Attachment(
            organization_id=workspace_id,
            issue_id=task_id,
            comment_id=payload.comment_id,
            uploaded_by_id=actor.id,
            object_key=payload.object_key,
            file_name=payload.file_name,
            content_type=payload.content_type,
            size_bytes=payload.size_bytes,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        await repository.add_attachment(attachment)
        return TaskAttachmentResponse.model_validate(attachment)

    async def list_attachments(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, actor: User) -> list[TaskAttachmentResponse]:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._get_task_required(repository, workspace_id, project_id, task_id)
        attachments = await repository.list_attachments(workspace_id, task_id)
        return [TaskAttachmentResponse.model_validate(attachment) for attachment in attachments]

    async def add_dependency(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskDependencyCreateRequest, actor: User) -> TaskDependencyResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._get_task_required(repository, workspace_id, project_id, task_id)
        await self._get_task_required(repository, workspace_id, project_id, payload.target_task_id)
        if task_id == payload.target_task_id:
            raise TaskValidationError("Task cannot depend on itself")
        if await repository.dependency_exists(task_id, payload.target_task_id, payload.link_type):
            raise TaskConflictError("Task dependency already exists")
        dependency = IssueLink(
            organization_id=workspace_id,
            source_issue_id=task_id,
            target_issue_id=payload.target_task_id,
            link_type=payload.link_type,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        await repository.add_dependency(dependency)
        return TaskDependencyResponse.model_validate(dependency)

    async def list_dependencies(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, actor: User) -> list[TaskDependencyResponse]:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        await self._get_task_required(repository, workspace_id, project_id, task_id)
        dependencies = await repository.list_dependencies(workspace_id, task_id)
        return [TaskDependencyResponse.model_validate(dependency) for dependency in dependencies]

    async def update_status(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskStatusUpdateRequest, actor: User) -> TaskResponse:
        return await self.update_task(session, workspace_id, project_id, task_id, TaskUpdateRequest(status_id=payload.status_id), actor)

    async def update_priority(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskPriorityUpdateRequest, actor: User) -> TaskResponse:
        return await self.update_task(session, workspace_id, project_id, task_id, TaskUpdateRequest(priority=payload.priority), actor)

    async def update_progress(self, session: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, payload: TaskProgressUpdateRequest, actor: User) -> TaskResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, project_id, actor.id)
        record = await self._get_task_required(repository, workspace_id, project_id, task_id, for_update=True)
        total = record.progress.checklist_total
        completed = record.progress.checklist_completed
        if payload.checklist_total is not None:
            total = payload.checklist_total
        if payload.checklist_completed is not None:
            completed = payload.checklist_completed
        if completed > total:
            raise TaskValidationError("Completed checklist count cannot exceed total count")
        if payload.percent_complete is not None:
            record.progress.percent_complete = payload.percent_complete
        record.progress.checklist_total = total
        record.progress.checklist_completed = completed
        if payload.is_blocked is not None:
            record.progress.is_blocked = payload.is_blocked
            if not payload.is_blocked:
                record.progress.blocked_reason = None
        if payload.blocked_reason is not None:
            if not record.progress.is_blocked:
                raise TaskValidationError("Blocked reason requires blocked status")
            record.progress.blocked_reason = payload.blocked_reason
        record.progress.updated_by_id = actor.id
        record.progress.version += 1
        await session.flush()
        return await self._build_response(repository, record)

    async def _require_member(self, repository: TaskRepository, workspace_id: uuid.UUID, project_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        if await repository.get_workspace(workspace_id) is None:
            raise TaskNotFoundError("Workspace not found")
        if await repository.get_project(workspace_id, project_id) is None:
            raise TaskNotFoundError("Project not found")
        membership_and_role = await repository.get_membership(workspace_id, actor_id)
        if membership_and_role is None:
            raise TaskPermissionError("Workspace membership required")
        membership, _role = membership_and_role
        if not is_active_membership(membership):
            raise TaskPermissionError("Active workspace membership required")

    async def _require_status(self, repository: TaskRepository, workspace_id: uuid.UUID, project_id: uuid.UUID, status_id: uuid.UUID) -> None:
        if await repository.get_status(workspace_id, project_id, status_id) is None:
            raise TaskValidationError("Task status is not valid for this project")

    async def _get_task_required(self, repository: TaskRepository, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, for_update: bool = False) -> TaskRecord:
        record = await repository.get_task_record(workspace_id, project_id, task_id, for_update=for_update)
        if record is None:
            raise TaskNotFoundError("Task not found")
        return record

    async def _assign_user(self, repository: TaskRepository, workspace_id: uuid.UUID, task_id: uuid.UUID, user_id: uuid.UUID, actor_id: uuid.UUID) -> IssueAssignee:
        membership = await repository.get_user_membership(workspace_id, user_id)
        if membership is None or not is_active_membership(membership):
            raise TaskValidationError("Assignee must be an active workspace member")
        existing = await repository.get_assignment(task_id, user_id)
        if existing is not None:
            return existing
        assignment = IssueAssignee(
            organization_id=workspace_id,
            issue_id=task_id,
            user_id=user_id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        return await repository.add_assignment(assignment)

    async def _attach_label(self, repository: TaskRepository, workspace_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, label_id: uuid.UUID, actor_id: uuid.UUID) -> IssueLabel:
        if await repository.get_label(workspace_id, project_id, label_id) is None:
            raise TaskNotFoundError("Label not found")
        existing = await repository.get_issue_label(task_id, label_id)
        if existing is not None:
            return existing
        issue_label = IssueLabel(
            organization_id=workspace_id,
            issue_id=task_id,
            label_id=label_id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        return await repository.add_issue_label(issue_label)

    async def _build_response(self, repository: TaskRepository, record: TaskRecord) -> TaskResponse:
        assignees = await repository.list_assignees(record.task.organization_id, record.task.id)
        labels = await repository.list_labels(record.task.organization_id, record.task.id)
        return TaskResponse(
            id=record.task.id,
            organization_id=record.task.organization_id,
            project_id=record.task.project_id,
            issue_number=record.task.issue_number,
            title=record.task.title,
            description=record.task.description,
            status_id=record.task.status_id,
            priority=record.task.priority,
            parent_task_id=record.task.parent_issue_id,
            due_at=record.task.due_at,
            story_points=float(record.task.story_points) if record.task.story_points is not None else None,
            progress=TaskProgressResponse(
                percent_complete=record.progress.percent_complete,
                checklist_total=record.progress.checklist_total,
                checklist_completed=record.progress.checklist_completed,
                is_blocked=record.progress.is_blocked,
                blocked_reason=record.progress.blocked_reason,
            ),
            assignees=[
                TaskAssigneeResponse(
                    user_id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    avatar_url=user.avatar_url,
                )
                for _assignment, user in assignees
            ],
            labels=[TaskLabelResponse.model_validate(label) for label in labels],
            created_at=record.task.created_at,
            updated_at=record.task.updated_at,
        )

    def _now(self) -> datetime:
        return datetime.now(UTC)


def get_task_service() -> TaskService:
    return TaskService()




