from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.models import Membership, Organization, Project, ProjectVisibility, Role

from .models import ProjectDetail, ProjectPriority, ProjectStatus


@dataclass(frozen=True)
class ProjectRecord:
    project: Project
    detail: ProjectDetail


class ProjectRepository:
    """Persistence boundary for project management use cases."""

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
        row = result.one_or_none()
        if row is None:
            return None
        membership, role = row
        return membership, role

    async def key_exists(
        self,
        workspace_id: uuid.UUID,
        key: str,
        exclude_project_id: uuid.UUID | None = None,
    ) -> bool:
        query = select(Project.id).where(
            Project.organization_id == workspace_id,
            Project.key == key,
            Project.deleted_at.is_(None),
        )
        if exclude_project_id is not None:
            query = query.where(Project.id != exclude_project_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def add_project(
        self,
        *,
        workspace_id: uuid.UUID,
        key: str,
        name: str,
        description: str | None,
        visibility: ProjectVisibility,
        actor_id: uuid.UUID,
    ) -> Project:
        project = Project(
            organization_id=workspace_id,
            key=key,
            name=name,
            description=description,
            visibility=visibility,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def add_detail(
        self,
        *,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        status: ProjectStatus,
        priority: ProjectPriority,
        starts_at,
        due_at,
        actor_id: uuid.UUID,
    ) -> ProjectDetail:
        detail = ProjectDetail(
            organization_id=workspace_id,
            project_id=project_id,
            status=status,
            priority=priority,
            starts_at=starts_at,
            due_at=due_at,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        self.session.add(detail)
        await self.session.flush()
        return detail

    async def get_project_record(self, workspace_id: uuid.UUID, project_id: uuid.UUID, for_update: bool = False) -> ProjectRecord | None:
        query = (
            select(Project, ProjectDetail)
            .join(ProjectDetail, ProjectDetail.project_id == Project.id)
            .where(
                Project.id == project_id,
                Project.organization_id == workspace_id,
                Project.deleted_at.is_(None),
                ProjectDetail.deleted_at.is_(None),
            )
        )
        if for_update:
            query = query.with_for_update()
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            return None
        project, detail = row
        return ProjectRecord(project=project, detail=detail)

    async def list_project_records(
        self,
        workspace_id: uuid.UUID,
        status: ProjectStatus | None = None,
        priority: ProjectPriority | None = None,
    ) -> list[ProjectRecord]:
        query = (
            select(Project, ProjectDetail)
            .join(ProjectDetail, ProjectDetail.project_id == Project.id)
            .where(
                Project.organization_id == workspace_id,
                Project.deleted_at.is_(None),
                ProjectDetail.deleted_at.is_(None),
            )
            .order_by(ProjectDetail.priority.desc(), Project.name.asc())
        )
        if status is not None:
            query = query.where(ProjectDetail.status == status)
        if priority is not None:
            query = query.where(ProjectDetail.priority == priority)
        result = await self.session.execute(query)
        return [ProjectRecord(project=project, detail=detail) for project, detail in result.all()]
