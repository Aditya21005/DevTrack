from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.models import (
    Commit,
    IntegrationConnection,
    IntegrationProvider,
    PullRequest,
    PullRequestState,
    Repository,
)

from .models import GitHubCommitMetadata, GitHubIssue, GitHubOAuthState, GitHubPullRequestMetadata, GitHubRepositoryMetadata


class GitHubRepositoryError(RuntimeError):
    """Raised when GitHub integration persistence fails."""


class GitHubIntegrationRepository:
    """Database-only repository for GitHub integration state and metadata."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_oauth_state(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        state_hash: str,
        code_verifier_hash: str,
        redirect_uri: str,
        scopes: list[str],
        expires_at: datetime,
    ) -> GitHubOAuthState:
        oauth_state = GitHubOAuthState(
            organization_id=organization_id,
            user_id=user_id,
            state_hash=state_hash,
            code_verifier_hash=code_verifier_hash,
            redirect_uri=redirect_uri,
            scopes=scopes,
            expires_at=expires_at,
        )
        self._session.add(oauth_state)
        await self._session.flush()
        return oauth_state

    async def get_oauth_state(self, *, state_hash: str) -> GitHubOAuthState | None:
        result = await self._session.execute(select(GitHubOAuthState).where(GitHubOAuthState.state_hash == state_hash))
        return result.scalar_one_or_none()

    async def get_oauth_state_for_update(self, *, state_hash: str) -> GitHubOAuthState | None:
        result = await self._session.execute(
            select(GitHubOAuthState).where(GitHubOAuthState.state_hash == state_hash).with_for_update()
        )
        return result.scalar_one_or_none()

    async def mark_oauth_state_consumed(self, oauth_state: GitHubOAuthState) -> None:
        oauth_state.consumed_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def upsert_connection(
        self,
        *,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
        external_account_id: str,
        display_name: str,
        encrypted_credentials: str,
        scopes: list[str],
    ) -> IntegrationConnection:
        result = await self._session.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.organization_id == organization_id,
                IntegrationConnection.provider == IntegrationProvider.github,
                IntegrationConnection.external_account_id == external_account_id,
                IntegrationConnection.deleted_at.is_(None),
            )
        )
        connection = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if connection is None:
            connection = IntegrationConnection(
                organization_id=organization_id,
                provider=IntegrationProvider.github,
                external_account_id=external_account_id,
                display_name=display_name,
                encrypted_credentials=encrypted_credentials,
                scopes=scopes,
                last_synced_at=now,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
            self._session.add(connection)
        else:
            connection.display_name = display_name
            connection.encrypted_credentials = encrypted_credentials
            connection.scopes = scopes
            connection.last_synced_at = now
            connection.updated_by_id = actor_id
            connection.version += 1

        await self._session.flush()
        return connection

    async def get_connection(self, *, connection_id: uuid.UUID, organization_id: uuid.UUID | None = None) -> IntegrationConnection | None:
        conditions = [
            IntegrationConnection.id == connection_id,
            IntegrationConnection.provider == IntegrationProvider.github,
            IntegrationConnection.deleted_at.is_(None),
        ]
        if organization_id is not None:
            conditions.append(IntegrationConnection.organization_id == organization_id)
        result = await self._session.execute(select(IntegrationConnection).where(*conditions))
        return result.scalar_one_or_none()

    async def get_repository(self, *, repository_id: uuid.UUID, organization_id: uuid.UUID | None = None) -> Repository | None:
        conditions = [Repository.id == repository_id, Repository.deleted_at.is_(None)]
        if organization_id is not None:
            conditions.append(Repository.organization_id == organization_id)
        result = await self._session.execute(select(Repository).where(*conditions))
        return result.scalar_one_or_none()

    async def upsert_repository(
        self,
        *,
        connection: IntegrationConnection,
        payload: dict[str, Any],
        project_id: uuid.UUID | None,
        actor_id: uuid.UUID | None,
        pushed_at: datetime | None,
    ) -> Repository:
        external_repository_id = str(payload["id"])
        result = await self._session.execute(
            select(Repository).where(
                Repository.integration_connection_id == connection.id,
                Repository.external_repository_id == external_repository_id,
                Repository.deleted_at.is_(None),
            )
        )
        repository = result.scalar_one_or_none()
        if repository is None:
            repository = Repository(
                organization_id=connection.organization_id,
                integration_connection_id=connection.id,
                project_id=project_id,
                external_repository_id=external_repository_id,
                full_name=payload["full_name"],
                default_branch=payload.get("default_branch"),
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
            self._session.add(repository)
            await self._session.flush()
        else:
            repository.project_id = project_id if project_id is not None else repository.project_id
            repository.full_name = payload["full_name"]
            repository.default_branch = payload.get("default_branch")
            repository.updated_by_id = actor_id
            repository.version += 1

        await self._upsert_repository_metadata(repository=repository, payload=payload, actor_id=actor_id, pushed_at=pushed_at)
        await self._session.flush()
        return repository

    async def upsert_commit(
        self,
        *,
        repository: Repository,
        payload: dict[str, Any],
        authored_at: datetime | None,
        committed_at: datetime | None,
    ) -> Commit:
        sha = payload["sha"]
        commit_payload = payload.get("commit") or {}
        author_payload = commit_payload.get("author") or {}
        committer_payload = commit_payload.get("committer") or {}

        result = await self._session.execute(
            select(Commit).where(Commit.repository_id == repository.id, Commit.sha == sha)
        )
        commit = result.scalar_one_or_none()
        if commit is None:
            commit = Commit(
                organization_id=repository.organization_id,
                repository_id=repository.id,
                sha=sha,
                message=commit_payload.get("message"),
                author_name=author_payload.get("name"),
                author_email=author_payload.get("email"),
                authored_at=authored_at,
            )
            self._session.add(commit)
            await self._session.flush()
        else:
            commit.message = commit_payload.get("message")
            commit.author_name = author_payload.get("name")
            commit.author_email = author_payload.get("email")
            commit.authored_at = authored_at

        await self._upsert_commit_metadata(
            commit=commit,
            payload=payload,
            committer_payload=committer_payload,
            committed_at=committed_at,
        )
        await self._session.flush()
        return commit

    async def upsert_issue(
        self,
        *,
        repository: Repository,
        payload: dict[str, Any],
        opened_at: datetime | None,
        closed_at: datetime | None,
        actor_id: uuid.UUID | None,
    ) -> GitHubIssue:
        number = int(payload["number"])
        result = await self._session.execute(
            select(GitHubIssue).where(GitHubIssue.repository_id == repository.id, GitHubIssue.number == number)
        )
        issue = result.scalar_one_or_none()
        author = payload.get("user") or {}
        labels = [self._compact_label(label) for label in payload.get("labels", [])]

        if issue is None:
            issue = GitHubIssue(
                organization_id=repository.organization_id,
                repository_id=repository.id,
                external_issue_id=str(payload["id"]),
                number=number,
                title=payload.get("title") or "Untitled GitHub issue",
                body=payload.get("body"),
                state=payload.get("state") or "unknown",
                author_external_id=str(author.get("id")) if author.get("id") is not None else None,
                html_url=payload.get("html_url"),
                labels=labels,
                opened_at=opened_at,
                closed_at=closed_at,
                raw_payload=payload,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
            self._session.add(issue)
        else:
            issue.external_issue_id = str(payload["id"])
            issue.title = payload.get("title") or issue.title
            issue.body = payload.get("body")
            issue.state = payload.get("state") or issue.state
            issue.author_external_id = str(author.get("id")) if author.get("id") is not None else None
            issue.html_url = payload.get("html_url")
            issue.labels = labels
            issue.opened_at = opened_at
            issue.closed_at = closed_at
            issue.raw_payload = payload
            issue.updated_by_id = actor_id
            issue.version += 1

        await self._session.flush()
        return issue

    async def upsert_pull_request(
        self,
        *,
        repository: Repository,
        payload: dict[str, Any],
        state: PullRequestState,
        opened_at: datetime | None,
        merged_at: datetime | None,
        closed_at: datetime | None,
        actor_id: uuid.UUID | None,
    ) -> PullRequest:
        number = int(payload["number"])
        result = await self._session.execute(
            select(PullRequest).where(PullRequest.repository_id == repository.id, PullRequest.number == number)
        )
        pull_request = result.scalar_one_or_none()
        author = payload.get("user") or {}
        head = payload.get("head") or {}
        base = payload.get("base") or {}

        if pull_request is None:
            pull_request = PullRequest(
                organization_id=repository.organization_id,
                repository_id=repository.id,
                number=number,
                title=payload.get("title") or "Untitled GitHub pull request",
                author_external_id=str(author.get("id")) if author.get("id") is not None else None,
                state=state,
                source_branch=head.get("ref"),
                target_branch=base.get("ref"),
                opened_at=opened_at,
                merged_at=merged_at,
                closed_at=closed_at,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
            self._session.add(pull_request)
            await self._session.flush()
        else:
            pull_request.title = payload.get("title") or pull_request.title
            pull_request.author_external_id = str(author.get("id")) if author.get("id") is not None else None
            pull_request.state = state
            pull_request.source_branch = head.get("ref")
            pull_request.target_branch = base.get("ref")
            pull_request.opened_at = opened_at
            pull_request.merged_at = merged_at
            pull_request.closed_at = closed_at
            pull_request.updated_by_id = actor_id
            pull_request.version += 1

        await self._upsert_pull_request_metadata(pull_request=pull_request, payload=payload, actor_id=actor_id)
        await self._session.flush()
        return pull_request

    async def touch_connection_synced(self, connection: IntegrationConnection) -> None:
        connection.last_synced_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def _upsert_repository_metadata(
        self,
        *,
        repository: Repository,
        payload: dict[str, Any],
        actor_id: uuid.UUID | None,
        pushed_at: datetime | None,
    ) -> GitHubRepositoryMetadata:
        result = await self._session.execute(
            select(GitHubRepositoryMetadata).where(GitHubRepositoryMetadata.repository_id == repository.id)
        )
        metadata = result.scalar_one_or_none()
        values = {
            "html_url": payload.get("html_url"),
            "clone_url": payload.get("clone_url"),
            "ssh_url": payload.get("ssh_url"),
            "visibility": payload.get("visibility"),
            "language": payload.get("language"),
            "is_private": bool(payload.get("private", False)),
            "is_fork": bool(payload.get("fork", False)),
            "pushed_at": pushed_at,
            "raw_payload": payload,
        }
        if metadata is None:
            metadata = GitHubRepositoryMetadata(repository_id=repository.id, created_by_id=actor_id, updated_by_id=actor_id, **values)
            self._session.add(metadata)
        else:
            for key, value in values.items():
                setattr(metadata, key, value)
            metadata.updated_by_id = actor_id
            metadata.version += 1
        return metadata

    async def _upsert_commit_metadata(
        self,
        *,
        commit: Commit,
        payload: dict[str, Any],
        committer_payload: dict[str, Any],
        committed_at: datetime | None,
    ) -> GitHubCommitMetadata:
        result = await self._session.execute(
            select(GitHubCommitMetadata).where(GitHubCommitMetadata.commit_id == commit.id)
        )
        metadata = result.scalar_one_or_none()
        values = {
            "html_url": payload.get("html_url"),
            "api_url": payload.get("url"),
            "committer_name": committer_payload.get("name"),
            "committer_email": committer_payload.get("email"),
            "committed_at": committed_at,
            "raw_payload": payload,
        }
        if metadata is None:
            metadata = GitHubCommitMetadata(commit_id=commit.id, **values)
            self._session.add(metadata)
        else:
            for key, value in values.items():
                setattr(metadata, key, value)
        return metadata

    async def _upsert_pull_request_metadata(
        self,
        *,
        pull_request: PullRequest,
        payload: dict[str, Any],
        actor_id: uuid.UUID | None,
    ) -> GitHubPullRequestMetadata:
        result = await self._session.execute(
            select(GitHubPullRequestMetadata).where(GitHubPullRequestMetadata.pull_request_id == pull_request.id)
        )
        metadata = result.scalar_one_or_none()
        values = {
            "external_pull_request_id": str(payload["id"]),
            "html_url": payload.get("html_url"),
            "body": payload.get("body"),
            "is_draft": bool(payload.get("draft", False)),
            "additions": payload.get("additions"),
            "deletions": payload.get("deletions"),
            "changed_files": payload.get("changed_files"),
            "raw_payload": payload,
        }
        if metadata is None:
            metadata = GitHubPullRequestMetadata(pull_request_id=pull_request.id, created_by_id=actor_id, updated_by_id=actor_id, **values)
            self._session.add(metadata)
        else:
            for key, value in values.items():
                setattr(metadata, key, value)
            metadata.updated_by_id = actor_id
            metadata.version += 1
        return metadata

    @staticmethod
    def _compact_label(label: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": label.get("id"),
            "name": label.get("name"),
            "color": label.get("color"),
            "description": label.get("description"),
        }

