from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class GitHubOAuthStart:
    authorization_url: str
    state: str
    code_verifier: str
    expires_at: datetime
    scopes: list[str]


@dataclass(frozen=True, slots=True)
class GitHubOAuthResult:
    connection_id: uuid.UUID
    organization_id: uuid.UUID
    external_account_id: str
    display_name: str
    scopes: list[str]


@dataclass(frozen=True, slots=True)
class GitHubRepositoryDTO:
    id: uuid.UUID
    full_name: str
    default_branch: str | None
    html_url: str | None
    visibility: str | None
    language: str | None


@dataclass(frozen=True, slots=True)
class GitHubCommitDTO:
    id: uuid.UUID
    repository_id: uuid.UUID
    sha: str
    message: str | None
    authored_at: datetime | None


@dataclass(frozen=True, slots=True)
class GitHubIssueDTO:
    id: uuid.UUID
    repository_id: uuid.UUID
    number: int
    title: str
    state: str
    html_url: str | None


@dataclass(frozen=True, slots=True)
class GitHubPullRequestDTO:
    id: uuid.UUID
    repository_id: uuid.UUID
    number: int
    title: str
    state: str
    html_url: str | None


@dataclass(frozen=True, slots=True)
class GitHubSyncResult:
    repositories_synced: int = 0
    commits_synced: int = 0
    issues_synced: int = 0
    pull_requests_synced: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
