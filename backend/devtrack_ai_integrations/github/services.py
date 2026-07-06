from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.models import IntegrationConnection, PullRequestState, Repository

from .client import GitHubClient, GitHubClientError
from .config import GitHubConfig
from .crypto import TokenCipher, TokenCryptoError
from .repositories import GitHubIntegrationRepository
from .schemas import GitHubOAuthResult, GitHubOAuthStart, GitHubSyncResult

logger = logging.getLogger(__name__)


class GitHubIntegrationError(RuntimeError):
    """Base GitHub integration domain error."""


class GitHubOAuthError(GitHubIntegrationError):
    """Raised when GitHub OAuth cannot be completed safely."""


class GitHubConnectionNotFoundError(GitHubIntegrationError):
    """Raised when a GitHub connection cannot be found."""


class GitHubRepositoryNotFoundError(GitHubIntegrationError):
    """Raised when a synchronized repository cannot be found."""


class GitHubCredentialError(GitHubIntegrationError):
    """Raised when encrypted GitHub credentials cannot be used."""


GitHubRepositoryFactory = Callable[[AsyncSession], GitHubIntegrationRepository]
GitHubClientFactory = Callable[[GitHubConfig], GitHubClient]


class GitHubIntegrationService:
    """Production service facade for GitHub OAuth and metadata sync."""

    _instance: "GitHubIntegrationService | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "GitHubIntegrationService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        config: GitHubConfig | None = None,
        repository_factory: GitHubRepositoryFactory = GitHubIntegrationRepository,
        client_factory: GitHubClientFactory = GitHubClient,
    ) -> None:
        if getattr(self, "_initialized", False):
            return
        self.config = config or GitHubConfig.from_env()
        self.repository_factory = repository_factory
        self.client_factory = client_factory
        self.cipher = TokenCipher(self.config.token_encryption_key)
        self._initialized = True

    async def start_oauth(
        self,
        session: AsyncSession,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        redirect_uri: str | None = None,
        scopes: list[str] | None = None,
    ) -> GitHubOAuthStart:
        effective_redirect_uri = redirect_uri or self.config.redirect_uri
        effective_scopes = scopes or self.config.scopes
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = self._pkce_challenge(code_verifier)
        expires_at = datetime.now(UTC) + timedelta(minutes=10)

        repository = self.repository_factory(session)
        await repository.create_oauth_state(
            organization_id=organization_id,
            user_id=user_id,
            state_hash=self._digest(state),
            code_verifier_hash=self._digest(code_verifier),
            redirect_uri=effective_redirect_uri,
            scopes=effective_scopes,
            expires_at=expires_at,
        )

        query = urlencode(
            {
                "client_id": self.config.client_id,
                "redirect_uri": effective_redirect_uri,
                "scope": " ".join(effective_scopes),
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        authorization_url = f"{self.config.oauth_authorize_url}?{query}"
        logger.info("github.oauth_started", extra={"organization_id": str(organization_id), "user_id": str(user_id)})
        return GitHubOAuthStart(
            authorization_url=authorization_url,
            state=state,
            code_verifier=code_verifier,
            expires_at=expires_at,
            scopes=effective_scopes,
        )

    async def complete_oauth(
        self,
        session: AsyncSession,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        code: str,
        state: str,
        code_verifier: str,
    ) -> GitHubOAuthResult:
        repository = self.repository_factory(session)
        state_hash = self._digest(state)
        verifier_hash = self._digest(code_verifier)
        oauth_state = await repository.get_oauth_state(state_hash=state_hash)
        self._validate_oauth_state(
            oauth_state,
            organization_id=organization_id,
            user_id=user_id,
            verifier_hash=verifier_hash,
        )

        client = self.client_factory(self.config)
        try:
            token_payload = await client.exchange_code(code=code, code_verifier=code_verifier, redirect_uri=oauth_state.redirect_uri)
            access_token = token_payload.get("access_token")
            if not access_token:
                raise GitHubOAuthError("GitHub did not return an access token")
            github_user = await client.get_authenticated_user(access_token)
        except GitHubClientError as exc:
            raise GitHubOAuthError("GitHub OAuth callback failed") from exc

        external_account_id = str(github_user.get("id"))
        if external_account_id == "None":
            raise GitHubOAuthError("GitHub user response did not include an id")
        display_name = github_user.get("login") or github_user.get("name") or external_account_id
        scopes = self._parse_scopes(token_payload.get("scope"), fallback=oauth_state.scopes)
        locked_oauth_state = await repository.get_oauth_state_for_update(state_hash=state_hash)
        self._validate_oauth_state(
            locked_oauth_state,
            organization_id=organization_id,
            user_id=user_id,
            verifier_hash=verifier_hash,
        )
        oauth_state = locked_oauth_state

        encrypted_credentials = self._encrypt_credentials(
            {
                "access_token": access_token,
                "token_type": token_payload.get("token_type", "bearer"),
                "scope": token_payload.get("scope"),
                "scopes": scopes,
                "github_user": {
                    "id": github_user.get("id"),
                    "login": github_user.get("login"),
                    "avatar_url": github_user.get("avatar_url"),
                    "html_url": github_user.get("html_url"),
                },
                "connected_at": datetime.now(UTC).isoformat(),
            }
        )
        connection = await repository.upsert_connection(
            organization_id=organization_id,
            actor_id=user_id,
            external_account_id=external_account_id,
            display_name=display_name,
            encrypted_credentials=encrypted_credentials,
            scopes=scopes,
        )
        await repository.mark_oauth_state_consumed(oauth_state)
        logger.info("github.oauth_completed", extra={"organization_id": str(organization_id), "connection_id": str(connection.id)})
        return GitHubOAuthResult(
            connection_id=connection.id,
            organization_id=organization_id,
            external_account_id=external_account_id,
            display_name=display_name,
            scopes=scopes,
        )

    async def sync_repositories(
        self,
        session: AsyncSession,
        *,
        connection_id: uuid.UUID,
        organization_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> GitHubSyncResult:
        repository = self.repository_factory(session)
        connection = await self._get_connection_required(repository, connection_id=connection_id, organization_id=organization_id)
        access_token = self._access_token(connection)
        client = self.client_factory(self.config)
        payloads = await client.list_authenticated_repositories(access_token)

        for payload in payloads:
            await repository.upsert_repository(
                connection=connection,
                payload=payload,
                project_id=project_id,
                actor_id=actor_id,
                pushed_at=self._parse_datetime(payload.get("pushed_at")),
            )
        await repository.touch_connection_synced(connection)
        logger.info("github.repositories_synced", extra={"connection_id": str(connection_id), "count": len(payloads)})
        return GitHubSyncResult(repositories_synced=len(payloads))

    async def sync_commits(
        self,
        session: AsyncSession,
        *,
        repository_id: uuid.UUID,
        organization_id: uuid.UUID,
        since: datetime | None = None,
    ) -> GitHubSyncResult:
        repo_repository = self.repository_factory(session)
        synced_repository = await self._get_repository_required(repo_repository, repository_id=repository_id, organization_id=organization_id)
        connection = await self._get_connection_required(repo_repository, connection_id=synced_repository.integration_connection_id, organization_id=organization_id)
        client = self.client_factory(self.config)
        payloads = await client.list_commits(self._access_token(connection), synced_repository.full_name, since=since.isoformat() if since else None)

        for payload in payloads:
            commit_payload = payload.get("commit") or {}
            await repo_repository.upsert_commit(
                repository=synced_repository,
                payload=payload,
                authored_at=self._parse_datetime((commit_payload.get("author") or {}).get("date")),
                committed_at=self._parse_datetime((commit_payload.get("committer") or {}).get("date")),
            )
        await repo_repository.touch_connection_synced(connection)
        logger.info("github.commits_synced", extra={"repository_id": str(repository_id), "count": len(payloads)})
        return GitHubSyncResult(commits_synced=len(payloads))

    async def sync_issues(
        self,
        session: AsyncSession,
        *,
        repository_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        state: str = "all",
    ) -> GitHubSyncResult:
        repo_repository = self.repository_factory(session)
        synced_repository = await self._get_repository_required(repo_repository, repository_id=repository_id, organization_id=organization_id)
        connection = await self._get_connection_required(repo_repository, connection_id=synced_repository.integration_connection_id, organization_id=organization_id)
        client = self.client_factory(self.config)
        payloads = await client.list_issues(self._access_token(connection), synced_repository.full_name, state=state)

        for payload in payloads:
            await repo_repository.upsert_issue(
                repository=synced_repository,
                payload=payload,
                opened_at=self._parse_datetime(payload.get("created_at")),
                closed_at=self._parse_datetime(payload.get("closed_at")),
                actor_id=actor_id,
            )
        await repo_repository.touch_connection_synced(connection)
        logger.info("github.issues_synced", extra={"repository_id": str(repository_id), "count": len(payloads)})
        return GitHubSyncResult(issues_synced=len(payloads))

    async def sync_pull_requests(
        self,
        session: AsyncSession,
        *,
        repository_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        state: str = "all",
    ) -> GitHubSyncResult:
        repo_repository = self.repository_factory(session)
        synced_repository = await self._get_repository_required(repo_repository, repository_id=repository_id, organization_id=organization_id)
        connection = await self._get_connection_required(repo_repository, connection_id=synced_repository.integration_connection_id, organization_id=organization_id)
        client = self.client_factory(self.config)
        payloads = await client.list_pull_requests(self._access_token(connection), synced_repository.full_name, state=state)

        for payload in payloads:
            await repo_repository.upsert_pull_request(
                repository=synced_repository,
                payload=payload,
                state=self._pull_request_state(payload),
                opened_at=self._parse_datetime(payload.get("created_at")),
                merged_at=self._parse_datetime(payload.get("merged_at")),
                closed_at=self._parse_datetime(payload.get("closed_at")),
                actor_id=actor_id,
            )
        await repo_repository.touch_connection_synced(connection)
        logger.info("github.pull_requests_synced", extra={"repository_id": str(repository_id), "count": len(payloads)})
        return GitHubSyncResult(pull_requests_synced=len(payloads))

    async def sync_repository_activity(
        self,
        session: AsyncSession,
        *,
        repository_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        commits_since: datetime | None = None,
    ) -> GitHubSyncResult:
        commits = await self.sync_commits(session, repository_id=repository_id, organization_id=organization_id, since=commits_since)
        issues = await self.sync_issues(session, repository_id=repository_id, organization_id=organization_id, actor_id=actor_id)
        pull_requests = await self.sync_pull_requests(session, repository_id=repository_id, organization_id=organization_id, actor_id=actor_id)
        return GitHubSyncResult(
            commits_synced=commits.commits_synced,
            issues_synced=issues.issues_synced,
            pull_requests_synced=pull_requests.pull_requests_synced,
        )

    def _validate_oauth_state(
        self,
        oauth_state: Any | None,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        verifier_hash: str,
    ) -> None:
        if oauth_state is None:
            raise GitHubOAuthError("Invalid GitHub OAuth state")
        if oauth_state.organization_id != organization_id or oauth_state.user_id != user_id:
            raise GitHubOAuthError("GitHub OAuth state does not belong to this actor")
        if oauth_state.consumed_at is not None:
            raise GitHubOAuthError("GitHub OAuth state has already been used")
        if oauth_state.expires_at <= datetime.now(UTC):
            raise GitHubOAuthError("GitHub OAuth state has expired")
        if not hmac.compare_digest(oauth_state.code_verifier_hash, verifier_hash):
            raise GitHubOAuthError("Invalid GitHub OAuth code verifier")

    async def _get_connection_required(
        self,
        repository: GitHubIntegrationRepository,
        *,
        connection_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> IntegrationConnection:
        connection = await repository.get_connection(connection_id=connection_id, organization_id=organization_id)
        if connection is None:
            raise GitHubConnectionNotFoundError("GitHub connection not found")
        return connection

    async def _get_repository_required(
        self,
        repository: GitHubIntegrationRepository,
        *,
        repository_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> Repository:
        synced_repository = await repository.get_repository(repository_id=repository_id, organization_id=organization_id)
        if synced_repository is None:
            raise GitHubRepositoryNotFoundError("GitHub repository not found")
        return synced_repository

    def _encrypt_credentials(self, payload: dict[str, Any]) -> str:
        try:
            return self.cipher.encrypt(json.dumps(payload, separators=(",", ":")))
        except TokenCryptoError as exc:
            raise GitHubCredentialError("Unable to encrypt GitHub credentials") from exc

    def _credentials(self, connection: IntegrationConnection) -> dict[str, Any]:
        try:
            return json.loads(self.cipher.decrypt(connection.encrypted_credentials))
        except (TokenCryptoError, json.JSONDecodeError) as exc:
            raise GitHubCredentialError("Unable to decrypt GitHub credentials") from exc

    def _access_token(self, connection: IntegrationConnection) -> str:
        access_token = self._credentials(connection).get("access_token")
        if not access_token:
            raise GitHubCredentialError("GitHub connection does not contain an access token")
        return str(access_token)

    def _digest(self, value: str) -> str:
        return hmac.new(self.config.token_encryption_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _pkce_challenge(code_verifier: str) -> str:
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    @staticmethod
    def _parse_scopes(scope_value: Any, *, fallback: list[str]) -> list[str]:
        if isinstance(scope_value, str) and scope_value.strip():
            return [scope.strip() for scope in scope_value.replace(",", " ").split() if scope.strip()]
        return fallback

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    @staticmethod
    def _pull_request_state(payload: dict[str, Any]) -> PullRequestState:
        if payload.get("draft"):
            return PullRequestState.draft
        if payload.get("merged_at"):
            return PullRequestState.merged
        state = payload.get("state")
        if state == "closed":
            return PullRequestState.closed
        return PullRequestState.open


def get_github_integration_service() -> GitHubIntegrationService:
    return GitHubIntegrationService()

