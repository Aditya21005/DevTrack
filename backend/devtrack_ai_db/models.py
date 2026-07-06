from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MembershipStatus(str, enum.Enum):
    invited = "invited"
    active = "active"
    suspended = "suspended"


class ProjectVisibility(str, enum.Enum):
    private = "private"
    organization = "organization"


class IssueType(str, enum.Enum):
    epic = "epic"
    story = "story"
    task = "task"
    bug = "bug"
    chore = "chore"


class IssuePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class IssueLinkType(str, enum.Enum):
    blocks = "blocks"
    relates_to = "relates_to"
    duplicates = "duplicates"
    parent_of = "parent_of"


class StatusCategory(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"


class SprintState(str, enum.Enum):
    planned = "planned"
    active = "active"
    closed = "closed"


class IntegrationProvider(str, enum.Enum):
    github = "github"
    gitlab = "gitlab"
    jira = "jira"
    slack = "slack"


class PullRequestState(str, enum.Enum):
    open = "open"
    closed = "closed"
    merged = "merged"
    draft = "draft"


class AIJobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class NotificationChannel(str, enum.Enum):
    in_app = "in_app"
    email = "email"
    slack = "slack"


class NotificationStatus(str, enum.Enum):
    unread = "unread"
    read = "read"
    archived = "archived"


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    restore = "restore"
    login = "login"
    permission_change = "permission_change"
    integration_change = "integration_change"
    ai_action = "ai_action"


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )


class AuditColumnsMixin(TimestampMixin):
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class TenantMixin:
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )


class Organization(UUIDPrimaryKeyMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (
        Index(
            "uq_organizations_slug_active",
            "slug",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    default_timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    memberships: Mapped[list[Membership]] = relationship(back_populates="organization")
    teams: Mapped[list[Team]] = relationship(back_populates="organization")
    projects: Mapped[list[Project]] = relationship(back_populates="organization")


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_email_active", "email", unique=True, postgresql_where=text("deleted_at IS NULL")),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="user",
        foreign_keys="Membership.user_id",
    )


class Role(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        Index(
            "uq_roles_org_name_active",
            "organization_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    permissions: Mapped[list[RolePermission]] = relationship(back_populates="role")


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list[RolePermission]] = relationship(back_populates="permission")


class RolePermission(TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),)

    role_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship(back_populates="roles")


class Membership(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        Index(
            "uq_memberships_org_user_active",
            "organization_id",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_memberships_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[MembershipStatus] = mapped_column(Enum(MembershipStatus, name="membership_status"), nullable=False)
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(
        back_populates="memberships",
        foreign_keys=[user_id],
    )
    role: Mapped[Role | None] = relationship()


class Team(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (
        Index(
            "uq_teams_org_name_active",
            "organization_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="teams")
    members: Mapped[list[TeamMembership]] = relationship(back_populates="team")


class TeamMembership(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "team_memberships"
    __table_args__ = (
        Index(
            "uq_team_memberships_team_user_active",
            "team_id",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    team: Mapped[Team] = relationship(back_populates="members")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class Project(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index(
            "uq_projects_org_key_active",
            "organization_id",
            "key",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_projects_org_name", "organization_id", "name"),
    )

    key: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[ProjectVisibility] = mapped_column(Enum(ProjectVisibility, name="project_visibility"), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="projects")
    members: Mapped[list[ProjectMember]] = relationship(back_populates="project")
    issues: Mapped[list[Issue]] = relationship(back_populates="project")


class ProjectMember(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "project_members"
    __table_args__ = (
        Index(
            "uq_project_members_project_user_active",
            "project_id",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    role: Mapped[Role | None] = relationship()


class Workflow(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "workflows"
    __table_args__ = (
        Index(
            "uq_workflows_project_name_active",
            "project_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    statuses: Mapped[list[WorkflowStatus]] = relationship(back_populates="workflow")


class WorkflowStatus(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "workflow_statuses"
    __table_args__ = (
        UniqueConstraint("workflow_id", "name", name="uq_workflow_statuses_workflow_name"),
        UniqueConstraint("workflow_id", "position", name="uq_workflow_statuses_workflow_position"),
        CheckConstraint("position >= 0", name="ck_workflow_statuses_position_non_negative"),
        Index("ix_workflow_statuses_org_category", "organization_id", "category"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[StatusCategory] = mapped_column(Enum(StatusCategory, name="status_category"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    workflow: Mapped[Workflow] = relationship(back_populates="statuses")


class Board(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "boards"
    __table_args__ = (
        Index(
            "uq_boards_project_name_active",
            "project_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    workflow_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    columns: Mapped[list[BoardColumn]] = relationship(back_populates="board")


class BoardColumn(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "board_columns"
    __table_args__ = (
        UniqueConstraint("board_id", "workflow_status_id", name="uq_board_columns_board_status"),
        UniqueConstraint("board_id", "position", name="uq_board_columns_board_position"),
        CheckConstraint("position >= 0", name="ck_board_columns_position_non_negative"),
    )

    board_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("boards.id", ondelete="RESTRICT"), nullable=False)
    workflow_status_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_statuses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    wip_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    board: Mapped[Board] = relationship(back_populates="columns")
    workflow_status: Mapped[WorkflowStatus] = relationship()


class Sprint(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "sprints"
    __table_args__ = (
        Index(
            "uq_sprints_project_name_active",
            "project_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_sprints_project_state", "project_id", "state"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    state: Mapped[SprintState] = mapped_column(Enum(SprintState, name="sprint_state"), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Milestone(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "milestones"
    __table_args__ = (
        Index(
            "uq_milestones_project_name_active",
            "project_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Label(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "labels"
    __table_args__ = (
        Index(
            "uq_labels_project_name_active",
            "project_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)


class Issue(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("project_id", "issue_number", name="uq_issues_project_number"),
        CheckConstraint("issue_number > 0", name="ck_issues_number_positive"),
        CheckConstraint("story_points IS NULL OR story_points >= 0", name="ck_issues_story_points_non_negative"),
        Index("ix_issues_org_project_status_rank", "organization_id", "project_id", "status_id", "rank"),
        Index("ix_issues_org_reporter", "organization_id", "reporter_id"),
        Index("ix_issues_org_sprint", "organization_id", "sprint_id"),
        Index("ix_issues_parent", "parent_issue_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_issue_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    status_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workflow_statuses.id", ondelete="RESTRICT"), nullable=False)
    sprint_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True)
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_type: Mapped[IssueType] = mapped_column(Enum(IssueType, name="issue_type"), nullable=False)
    priority: Mapped[IssuePriority] = mapped_column(Enum(IssuePriority, name="issue_priority"), nullable=False)
    rank: Mapped[str] = mapped_column(String(64), nullable=False)
    story_points: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="issues")
    parent_issue: Mapped[Issue | None] = relationship(remote_side="Issue.id")
    status: Mapped[WorkflowStatus] = relationship()
    assignees: Mapped[list[IssueAssignee]] = relationship(back_populates="issue")
    comments: Mapped[list[Comment]] = relationship(back_populates="issue")


class IssueAssignee(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "issue_assignees"
    __table_args__ = (
        Index(
            "uq_issue_assignees_issue_user_active",
            "issue_id",
            "user_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_issue_assignees_org_user", "organization_id", "user_id"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="assignees")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class IssueLabel(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "issue_labels"
    __table_args__ = (
        Index(
            "uq_issue_labels_issue_label_active",
            "issue_id",
            "label_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False)
    label_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("labels.id", ondelete="RESTRICT"), nullable=False)


class IssueLink(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "issue_links"
    __table_args__ = (
        UniqueConstraint("source_issue_id", "target_issue_id", "link_type", name="uq_issue_links_source_target_type"),
        CheckConstraint("source_issue_id <> target_issue_id", name="ck_issue_links_no_self_link"),
    )

    source_issue_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False)
    target_issue_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False)
    link_type: Mapped[IssueLinkType] = mapped_column(Enum(IssueLinkType, name="issue_link_type"), nullable=False)


class Comment(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_issue_created", "issue_id", "created_at"),
        Index("ix_comments_org_author", "organization_id", "author_id"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="comments")
    author: Mapped[User | None] = relationship(foreign_keys=[author_id])


class Attachment(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "attachments"
    __table_args__ = (Index("ix_attachments_issue", "issue_id"),)

    issue_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=True)
    comment_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("comments.id", ondelete="RESTRICT"), nullable=True)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)


class ActivityEvent(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "activity_events"
    __table_args__ = (
        Index("ix_activity_events_org_created", "organization_id", "created_at"),
        Index("ix_activity_events_issue_created", "issue_id", "created_at"),
    )

    issue_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class IntegrationConnection(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "integration_connections"
    __table_args__ = (
        Index(
            "uq_integration_connections_org_provider_external_active",
            "organization_id",
            "provider",
            "external_account_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider, name="integration_provider"), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default=text("ARRAY[]::varchar[]"))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookEvent(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_webhook_events_provider_external"),
        Index("ix_webhook_events_org_processed", "organization_id", "processed_at"),
    )

    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider, name="integration_provider"), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(240), nullable=False)
    headers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Repository(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "repositories"
    __table_args__ = (
        Index(
            "uq_repositories_connection_external_active",
            "integration_connection_id",
            "external_repository_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    integration_connection_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_connections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    external_repository_id: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(120), nullable=True)


class PullRequest(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repository_id", "number", name="uq_pull_requests_repository_number"),
        Index("ix_pull_requests_org_state", "organization_id", "state"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author_external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[PullRequestState] = mapped_column(Enum(PullRequestState, name="pull_request_state"), nullable=False)
    source_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Commit(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "commits"
    __table_args__ = (
        UniqueConstraint("repository_id", "sha", name="uq_commits_repository_sha"),
        Index("ix_commits_org_authored", "organization_id", "authored_at"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False)
    sha: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    authored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PullRequestIssue(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "pull_request_issues"
    __table_args__ = (
        Index(
            "uq_pull_request_issues_pr_issue_active",
            "pull_request_id",
            "issue_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    pull_request_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("pull_requests.id", ondelete="RESTRICT"), nullable=False)
    issue_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="RESTRICT"), nullable=False)


class AIConversation(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (Index("ix_ai_conversations_org_user", "organization_id", "user_id"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)


class AIMessage(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "ai_messages"
    __table_args__ = (Index("ix_ai_messages_conversation_created", "conversation_id", "created_at"),)

    conversation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="RESTRICT"), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AIJob(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("ix_ai_jobs_org_status_created", "organization_id", "status", "created_at"),
        Index("ix_ai_jobs_requested_by", "requested_by_id"),
    )

    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    issue_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    job_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[AIJobStatus] = mapped_column(Enum(AIJobStatus, name="ai_job_status"), nullable=False)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AIArtifact(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    __tablename__ = "ai_artifacts"
    __table_args__ = (Index("ix_ai_artifacts_job", "ai_job_id"),)

    ai_job_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ai_jobs.id", ondelete="RESTRICT"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    accepted_by_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Embedding(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("source_table", "source_id", "chunk_index", "model", name="uq_embeddings_source_chunk_model"),
        Index("ix_embeddings_org_source", "organization_id", "source_table", "source_id"),
    )

    source_table: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)


class Notification(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_status_created", "user_id", "status", "created_at"),
        Index("ix_notifications_org_created", "organization_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel"), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus, name="notification_status"), nullable=False)
    subject: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_created", "organization_id", "created_at"),
        Index("ix_audit_logs_org_actor", "organization_id", "actor_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

    actor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
