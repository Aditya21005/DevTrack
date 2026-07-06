from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devtrack_ai_db.models import AuditColumnsMixin, Base, Project, SoftDeleteMixin, TenantMixin, UUIDPrimaryKeyMixin


class ProjectStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    canceled = "canceled"
    archived = "archived"


class ProjectPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ProjectDetail(UUIDPrimaryKeyMixin, TenantMixin, AuditColumnsMixin, SoftDeleteMixin, Base):
    """Project management metadata stored beside the shared Project aggregate."""

    __tablename__ = "project_details"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_details_project"),
        CheckConstraint("starts_at IS NULL OR due_at IS NULL OR starts_at <= due_at", name="ck_project_details_dates_order"),
        Index("ix_project_details_org_status_priority", "organization_id", "status", "priority"),
        Index("ix_project_details_due_at", "due_at"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus, name="project_status"), nullable=False)
    priority: Mapped[ProjectPriority] = mapped_column(Enum(ProjectPriority, name="project_priority"), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(foreign_keys=[project_id])
