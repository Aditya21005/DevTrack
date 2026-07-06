from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devtrack_ai_db.models import AuditColumnsMixin, Base, Commit, PullRequest, Repository, TimestampMixin, UUIDPrimaryKeyMixin


class GitHubOAuthState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_oauth_states"
    __table_args__ = (
        Index("uq_github_oauth_states_state_hash", "state_hash", unique=True),
        Index("ix_github_oauth_states_org_expires", "organization_id", "expires_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    code_verifier_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GitHubRepositoryMetadata(UUIDPrimaryKeyMixin, AuditColumnsMixin, Base):
    __tablename__ = "github_repository_metadata"
    __table_args__ = (UniqueConstraint("repository_id", name="uq_github_repository_metadata_repository"),)

    repository_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    clone_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ssh_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str | None] = mapped_column(String(40), nullable=True)
    language: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_fork: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    repository: Mapped[Repository] = relationship(foreign_keys=[repository_id])


class GitHubCommitMetadata(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "github_commit_metadata"
    __table_args__ = (UniqueConstraint("commit_id", name="uq_github_commit_metadata_commit"),)

    commit_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    committer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    committer_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    commit: Mapped[Commit] = relationship(foreign_keys=[commit_id])


class GitHubIssue(UUIDPrimaryKeyMixin, AuditColumnsMixin, Base):
    __tablename__ = "github_issues"
    __table_args__ = (
        UniqueConstraint("repository_id", "number", name="uq_github_issues_repository_number"),
        Index("ix_github_issues_org_state", "organization_id", "state"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    repository_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    external_issue_id: Mapped[str] = mapped_column(String(200), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    author_external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    labels: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class GitHubPullRequestMetadata(UUIDPrimaryKeyMixin, AuditColumnsMixin, Base):
    __tablename__ = "github_pull_request_metadata"
    __table_args__ = (UniqueConstraint("pull_request_id", name="uq_github_pull_request_metadata_pr"),)

    pull_request_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    external_pull_request_id: Mapped[str] = mapped_column(String(200), nullable=False)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    additions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deletions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    changed_files: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    pull_request: Mapped[PullRequest] = relationship(foreign_keys=[pull_request_id])
