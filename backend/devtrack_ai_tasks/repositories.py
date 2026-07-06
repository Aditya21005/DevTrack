from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.models import (
    Attachment,
    Comment,
    Issue,
    IssueAssignee,
    IssueLabel,
    IssueLink,
    IssueLinkType,
    IssueType,
    Label,
    Membership,
    Organization,
    Project,
    Role,
    User,
    Workflow,
    WorkflowStatus,
)

from .models import TaskProgress


@dataclass(frozen=True)
class TaskRecord:
    task: Issue
    progress: TaskProgress


class TaskRepository:
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

    async def get_user_membership(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> Membership | None:
        result = await self.session.execute(
            select(Membership).where(
                Membership.organization_id == workspace_id,
                Membership.user_id == user_id,
                Membership.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_status(self, workspace_id: uuid.UUID, project_id: uuid.UUID, status_id: uuid.UUID) -> WorkflowStatus | None:
        result = await self.session.execute(
            select(WorkflowStatus)
            .join(Workflow, WorkflowStatus.workflow_id == Workflow.id)
            .where(
                WorkflowStatus.id == status_id,
                WorkflowStatus.organization_id == workspace_id,
                WorkflowStatus.deleted_at.is_(None),
                Workflow.project_id == project_id,
                Workflow.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_task_record(
        self,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        for_update: bool = False,
    ) -> TaskRecord | None:
        query = (
            select(Issue, TaskProgress)
            .join(TaskProgress, TaskProgress.issue_id == Issue.id)
            .where(
                Issue.id == task_id,
                Issue.organization_id == workspace_id,
                Issue.project_id == project_id,
                Issue.issue_type == IssueType.task,
                Issue.deleted_at.is_(None),
                TaskProgress.deleted_at.is_(None),
            )
        )
        if for_update:
            query = query.with_for_update()
        result = await self.session.execute(query)
        row = result.one_or_none()
        if row is None:
            return None
        task, progress = row
        return TaskRecord(task=task, progress=progress)

    async def list_task_records(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> list[TaskRecord]:
        result = await self.session.execute(
            select(Issue, TaskProgress)
            .join(TaskProgress, TaskProgress.issue_id == Issue.id)
            .where(
                Issue.organization_id == workspace_id,
                Issue.project_id == project_id,
                Issue.issue_type == IssueType.task,
                Issue.deleted_at.is_(None),
                TaskProgress.deleted_at.is_(None),
            )
            .order_by(Issue.rank.asc(), Issue.issue_number.asc())
        )
        return [TaskRecord(task=task, progress=progress) for task, progress in result.all()]

    async def next_issue_number(self, project_id: uuid.UUID) -> int:
        result = await self.session.execute(select(func.coalesce(func.max(Issue.issue_number), 0)).where(Issue.project_id == project_id))
        return int(result.scalar_one()) + 1

    async def add_task(self, task: Issue) -> Issue:
        self.session.add(task)
        await self.session.flush()
        return task

    async def add_progress(self, progress: TaskProgress) -> TaskProgress:
        self.session.add(progress)
        await self.session.flush()
        return progress

    async def get_label(self, workspace_id: uuid.UUID, project_id: uuid.UUID, label_id: uuid.UUID) -> Label | None:
        label = await self.session.get(Label, label_id)
        if label is None or label.deleted_at is not None or label.organization_id != workspace_id or label.project_id != project_id:
            return None
        return label

    async def label_name_exists(self, workspace_id: uuid.UUID, project_id: uuid.UUID, name: str) -> bool:
        result = await self.session.execute(
            select(Label.id).where(
                Label.organization_id == workspace_id,
                Label.project_id == project_id,
                func.lower(Label.name) == name.lower(),
                Label.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_label(self, label: Label) -> Label:
        self.session.add(label)
        await self.session.flush()
        return label

    async def get_issue_label(self, task_id: uuid.UUID, label_id: uuid.UUID) -> IssueLabel | None:
        result = await self.session.execute(
            select(IssueLabel).where(IssueLabel.issue_id == task_id, IssueLabel.label_id == label_id, IssueLabel.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def add_issue_label(self, issue_label: IssueLabel) -> IssueLabel:
        self.session.add(issue_label)
        await self.session.flush()
        return issue_label

    async def get_assignment(self, task_id: uuid.UUID, user_id: uuid.UUID) -> IssueAssignee | None:
        result = await self.session.execute(
            select(IssueAssignee).where(
                IssueAssignee.issue_id == task_id,
                IssueAssignee.user_id == user_id,
                IssueAssignee.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def add_assignment(self, assignment: IssueAssignee) -> IssueAssignee:
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def get_comment(self, workspace_id: uuid.UUID, task_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
        comment = await self.session.get(Comment, comment_id)
        if comment is None or comment.deleted_at is not None or comment.organization_id != workspace_id or comment.issue_id != task_id:
            return None
        return comment

    async def add_comment(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def list_comments(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> list[Comment]:
        result = await self.session.execute(
            select(Comment)
            .where(Comment.organization_id == workspace_id, Comment.issue_id == task_id, Comment.deleted_at.is_(None))
            .order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def add_attachment(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.flush()
        return attachment

    async def list_attachments(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> list[Attachment]:
        result = await self.session.execute(
            select(Attachment)
            .where(Attachment.organization_id == workspace_id, Attachment.issue_id == task_id, Attachment.deleted_at.is_(None))
            .order_by(Attachment.created_at.desc())
        )
        return list(result.scalars().all())

    async def dependency_exists(self, source_task_id: uuid.UUID, target_task_id: uuid.UUID, link_type: IssueLinkType) -> bool:
        result = await self.session.execute(
            select(IssueLink.id).where(
                IssueLink.source_issue_id == source_task_id,
                IssueLink.target_issue_id == target_task_id,
                IssueLink.link_type == link_type,
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_dependency(self, dependency: IssueLink) -> IssueLink:
        self.session.add(dependency)
        await self.session.flush()
        return dependency

    async def list_dependencies(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> list[IssueLink]:
        result = await self.session.execute(
            select(IssueLink).where(IssueLink.organization_id == workspace_id, IssueLink.source_issue_id == task_id)
        )
        return list(result.scalars().all())

    async def list_assignees(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> list[tuple[IssueAssignee, User]]:
        result = await self.session.execute(
            select(IssueAssignee, User)
            .join(User, IssueAssignee.user_id == User.id)
            .where(
                IssueAssignee.organization_id == workspace_id,
                IssueAssignee.issue_id == task_id,
                IssueAssignee.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(User.display_name.asc())
        )
        return list(result.all())

    async def list_labels(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> list[Label]:
        result = await self.session.execute(
            select(Label)
            .join(IssueLabel, IssueLabel.label_id == Label.id)
            .where(
                IssueLabel.organization_id == workspace_id,
                IssueLabel.issue_id == task_id,
                IssueLabel.deleted_at.is_(None),
                Label.deleted_at.is_(None),
            )
            .order_by(Label.name.asc())
        )
        return list(result.scalars().all())
