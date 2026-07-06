from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devtrack_ai_db.models import (
    Attachment,
    AuditColumnsMixin,
    Base,
    Comment,
    Issue,
    IssueAssignee,
    IssueLabel,
    IssueLink,
    Label,
    SoftDeleteMixin,
    TenantMixin,
    UUIDPrimaryKeyMixin,
)

Task = Issue
TaskAssignee = IssueAssignee
TaskAttachment = Attachment
TaskComment = Comment
TaskDependency = IssueLink
TaskLabel = Label
TaskLabelLink = IssueLabel


class TaskProgress(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    """Task progress metadata stored beside the shared Issue aggregate."""

    __tablename__ = "task_progress"
    __table_args__ = (
        UniqueConstraint("issue_id", name="uq_task_progress_issue"),
        CheckConstraint("percent_complete >= 0 AND percent_complete <= 100", name="ck_task_progress_percent_range"),
        CheckConstraint("checklist_total >= 0", name="ck_task_progress_checklist_total_non_negative"),
        CheckConstraint("checklist_completed >= 0", name="ck_task_progress_checklist_completed_non_negative"),
        CheckConstraint("checklist_completed <= checklist_total", name="ck_task_progress_checklist_completed_lte_total"),
        Index("ix_task_progress_org_percent", "organization_id", "percent_complete"),
        Index("ix_task_progress_blocked", "organization_id", "is_blocked"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
    )
    percent_complete: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    checklist_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    checklist_completed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    task: Mapped[Issue] = relationship(foreign_keys=[issue_id])
