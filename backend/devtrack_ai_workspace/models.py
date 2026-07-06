from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devtrack_ai_db.models import AuditColumnsMixin, Base, Organization, Role, User, UUIDPrimaryKeyMixin


# Workspace is the product term for the tenant root stored as Organization.
Workspace = Organization
WorkspaceMember = User
WorkspaceRole = Role


class WorkspaceInvitation(UUIDPrimaryKeyMixin, AuditColumnsMixin, Base):
    """Email invitation to join a workspace.

    The invitation is separate from memberships so teams can invite people before
    they have registered. The raw token is never stored; only a hash belongs in
    the database.
    """

    __tablename__ = "workspace_invitations"
    __table_args__ = (
        Index(
            "uq_workspace_invitations_org_email_active",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=text("accepted_at IS NULL AND revoked_at IS NULL"),
        ),
        Index("ix_workspace_invitations_org_expires", "organization_id", "expires_at"),
        Index("uq_workspace_invitations_token_hash", "token_hash", unique=True),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    workspace: Mapped[Organization] = relationship(foreign_keys=[organization_id])
    role: Mapped[Role | None] = relationship(foreign_keys=[role_id])
    revoked_by: Mapped[User | None] = relationship(foreign_keys=[revoked_by_id])
