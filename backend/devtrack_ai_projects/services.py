from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.access_control import has_admin_role, is_active_membership
from devtrack_ai_db.models import ProjectVisibility, User

from .models import ProjectDetail, ProjectPriority, ProjectStatus
from .repositories import ProjectRecord, ProjectRepository
from .schemas import (
    ProjectCreateRequest,
    ProjectDeadlineUpdateRequest,
    ProjectPriorityUpdateRequest,
    ProjectResponse,
    ProjectStatusUpdateRequest,
    ProjectUpdateRequest,
)

logger = logging.getLogger(__name__)

ALLOWED_STATUS_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.planned: {ProjectStatus.active, ProjectStatus.canceled},
    ProjectStatus.active: {ProjectStatus.on_hold, ProjectStatus.completed, ProjectStatus.canceled},
    ProjectStatus.on_hold: {ProjectStatus.active, ProjectStatus.canceled},
    ProjectStatus.completed: {ProjectStatus.archived},
    ProjectStatus.canceled: {ProjectStatus.archived},
    ProjectStatus.archived: set(),
}


class ProjectError(RuntimeError):
    """Base project domain error."""


class ProjectNotFoundError(ProjectError):
    """Raised when a workspace or project cannot be found."""


class ProjectConflictError(ProjectError):
    """Raised when project data conflicts with existing state."""


class ProjectPermissionError(ProjectError):
    """Raised when the actor lacks project permissions."""


class ProjectValidationError(ProjectError):
    """Raised when project data violates business rules."""


ProjectRepositoryFactory = Callable[[AsyncSession], ProjectRepository]


class ProjectService:
    def __init__(self, repository_factory: ProjectRepositoryFactory = ProjectRepository) -> None:
        self.repository_factory = repository_factory

    async def create_project(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        payload: ProjectCreateRequest,
        actor: User,
    ) -> ProjectResponse:
        repository = self.repository_factory(session)
        await self._require_admin(repository, workspace_id, actor.id)
        self._validate_create_status(payload.status)
        self._validate_deadlines(payload.starts_at, payload.due_at)
        await self._ensure_key_available(repository, workspace_id, payload.key)

        project = await repository.add_project(
            workspace_id=workspace_id,
            key=payload.key,
            name=payload.name,
            description=payload.description,
            visibility=ProjectVisibility(payload.visibility),
            actor_id=actor.id,
        )
        detail = await repository.add_detail(
            workspace_id=workspace_id,
            project_id=project.id,
            status=payload.status,
            priority=payload.priority,
            starts_at=payload.starts_at,
            due_at=payload.due_at,
            actor_id=actor.id,
        )

        logger.info("project.created", extra={"workspace_id": str(workspace_id), "project_id": str(project.id)})
        return self._to_response(ProjectRecord(project=project, detail=detail))

    async def list_projects(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        actor: User,
        status: ProjectStatus | None = None,
        priority: ProjectPriority | None = None,
    ) -> list[ProjectResponse]:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, actor.id)
        records = await repository.list_project_records(workspace_id, status=status, priority=priority)
        return [self._to_response(record) for record in records]

    async def get_project(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        actor: User,
    ) -> ProjectResponse:
        repository = self.repository_factory(session)
        await self._require_member(repository, workspace_id, actor.id)
        record = await self._get_project_record_required(repository, workspace_id, project_id)
        return self._to_response(record)

    async def update_project(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        payload: ProjectUpdateRequest,
        actor: User,
    ) -> ProjectResponse:
        repository = self.repository_factory(session)
        await self._require_admin(repository, workspace_id, actor.id)
        record = await self._get_project_record_required(repository, workspace_id, project_id, for_update=True)

        updated_starts_at = record.detail.starts_at
        updated_due_at = record.detail.due_at
        fields = payload.model_fields_set
        if "starts_at" in fields:
            updated_starts_at = payload.starts_at
        if "due_at" in fields:
            updated_due_at = payload.due_at
        self._validate_deadlines(updated_starts_at, updated_due_at)

        if payload.key is not None and payload.key != record.project.key:
            await self._ensure_key_available(repository, workspace_id, payload.key, exclude_project_id=project_id)
            record.project.key = payload.key
        if "name" in fields and payload.name is not None:
            record.project.name = payload.name
        if "description" in fields:
            record.project.description = payload.description
        if payload.visibility is not None:
            record.project.visibility = ProjectVisibility(payload.visibility)
        if payload.status is not None:
            self._apply_status_transition(record.detail, payload.status)
        if payload.priority is not None:
            record.detail.priority = payload.priority
        if "starts_at" in fields:
            record.detail.starts_at = payload.starts_at
        if "due_at" in fields:
            record.detail.due_at = payload.due_at

        record.project.updated_by_id = actor.id
        record.project.version += 1
        record.detail.updated_by_id = actor.id
        record.detail.version += 1
        await session.flush()

        logger.info("project.updated", extra={"workspace_id": str(workspace_id), "project_id": str(project_id)})
        return self._to_response(record)

    async def update_status(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        payload: ProjectStatusUpdateRequest,
        actor: User,
    ) -> ProjectResponse:
        return await self.update_project(
            session,
            workspace_id,
            project_id,
            ProjectUpdateRequest(status=payload.status),
            actor,
        )

    async def update_deadlines(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        payload: ProjectDeadlineUpdateRequest,
        actor: User,
    ) -> ProjectResponse:
        update_payload = ProjectUpdateRequest()
        update_payload.starts_at = payload.starts_at
        update_payload.due_at = payload.due_at
        update_payload.model_fields_set.update({"starts_at", "due_at"})
        return await self.update_project(session, workspace_id, project_id, update_payload, actor)

    async def update_priority(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        payload: ProjectPriorityUpdateRequest,
        actor: User,
    ) -> ProjectResponse:
        return await self.update_project(
            session,
            workspace_id,
            project_id,
            ProjectUpdateRequest(priority=payload.priority),
            actor,
        )

    async def delete_project(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        actor: User,
    ) -> None:
        repository = self.repository_factory(session)
        await self._require_admin(repository, workspace_id, actor.id)
        record = await self._get_project_record_required(repository, workspace_id, project_id, for_update=True)
        now = self._now()
        record.project.deleted_at = now
        record.project.deleted_by_id = actor.id
        record.project.updated_by_id = actor.id
        record.project.version += 1
        record.detail.deleted_at = now
        record.detail.deleted_by_id = actor.id
        record.detail.updated_by_id = actor.id
        record.detail.version += 1
        await session.flush()
        logger.info("project.deleted", extra={"workspace_id": str(workspace_id), "project_id": str(project_id)})

    async def _require_member(self, repository: ProjectRepository, workspace_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        workspace = await repository.get_workspace(workspace_id)
        if workspace is None:
            raise ProjectNotFoundError("Workspace not found")
        membership_and_role = await repository.get_membership(workspace_id, actor_id)
        if membership_and_role is None:
            raise ProjectPermissionError("Workspace membership required")
        membership, _role = membership_and_role
        if not is_active_membership(membership):
            raise ProjectPermissionError("Active workspace membership required")

    async def _require_admin(self, repository: ProjectRepository, workspace_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        await self._require_member(repository, workspace_id, actor_id)
        membership_and_role = await repository.get_membership(workspace_id, actor_id)
        if membership_and_role is None:
            raise ProjectPermissionError("Workspace admin permission required")
        _membership, role = membership_and_role
        if not has_admin_role(role):
            raise ProjectPermissionError("Workspace admin permission required")

    async def _get_project_record_required(
        self,
        repository: ProjectRepository,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        for_update: bool = False,
    ) -> ProjectRecord:
        record = await repository.get_project_record(workspace_id, project_id, for_update=for_update)
        if record is None:
            raise ProjectNotFoundError("Project not found")
        return record

    async def _ensure_key_available(
        self,
        repository: ProjectRepository,
        workspace_id: uuid.UUID,
        key: str,
        exclude_project_id: uuid.UUID | None = None,
    ) -> None:
        if await repository.key_exists(workspace_id, key, exclude_project_id=exclude_project_id):
            raise ProjectConflictError("Project key is already in use")

    def _validate_create_status(self, status: ProjectStatus) -> None:
        if status in {ProjectStatus.completed, ProjectStatus.archived}:
            raise ProjectValidationError("New projects cannot start as completed or archived")

    def _validate_deadlines(self, starts_at, due_at) -> None:
        if starts_at is not None and due_at is not None and starts_at > due_at:
            raise ProjectValidationError("Project start date cannot be after due date")

    def _apply_status_transition(self, detail: ProjectDetail, new_status: ProjectStatus) -> None:
        current_status = detail.status
        if new_status == current_status:
            return
        if new_status not in ALLOWED_STATUS_TRANSITIONS[current_status]:
            raise ProjectValidationError(f"Cannot move project from {current_status.value} to {new_status.value}")
        now = self._now()
        detail.status = new_status
        if new_status == ProjectStatus.completed:
            detail.completed_at = now
        elif current_status == ProjectStatus.completed:
            detail.completed_at = None
        if new_status == ProjectStatus.archived:
            detail.archived_at = now

    def _to_response(self, record: ProjectRecord) -> ProjectResponse:
        return ProjectResponse(
            id=record.project.id,
            organization_id=record.project.organization_id,
            key=record.project.key,
            name=record.project.name,
            description=record.project.description,
            visibility=record.project.visibility.value,
            status=record.detail.status,
            priority=record.detail.priority,
            starts_at=record.detail.starts_at,
            due_at=record.detail.due_at,
            completed_at=record.detail.completed_at,
            archived_at=record.detail.archived_at,
            created_at=record.project.created_at,
            updated_at=record.project.updated_at,
        )

    def _now(self) -> datetime:
        return datetime.now(UTC)


def get_project_service() -> ProjectService:
    return ProjectService()


