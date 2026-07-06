from __future__ import annotations

import os
from dataclasses import dataclass


class GitHubConfigurationError(RuntimeError):
    """Raised when GitHub integration configuration is invalid."""


@dataclass(frozen=True)
class GitHubConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: tuple[str, ...]
    token_encryption_key: str
    api_base_url: str = "https://api.github.com"
    oauth_authorize_url: str = "https://github.com/login/oauth/authorize"
    oauth_token_url: str = "https://github.com/login/oauth/access_token"
    timeout_seconds: float = 30.0
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        client_id = os.getenv("GITHUB_CLIENT_ID", "").strip()
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "").strip()
        token_encryption_key = os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY", "").strip()
        if not client_id:
            raise GitHubConfigurationError("GITHUB_CLIENT_ID is required")
        if not client_secret:
            raise GitHubConfigurationError("GITHUB_CLIENT_SECRET is required")
        if not redirect_uri:
            raise GitHubConfigurationError("GITHUB_REDIRECT_URI is required")
        if not token_encryption_key:
            raise GitHubConfigurationError("GITHUB_TOKEN_ENCRYPTION_KEY is required")
        scopes = tuple(scope for scope in os.getenv("GITHUB_OAUTH_SCOPES", "repo read:user user:email").split() if scope)
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            token_encryption_key=token_encryption_key,
            api_base_url=os.getenv("GITHUB_API_BASE_URL", "https://api.github.com").rstrip("/"),
            oauth_authorize_url=os.getenv("GITHUB_OAUTH_AUTHORIZE_URL", "https://github.com/login/oauth/authorize"),
            oauth_token_url=os.getenv("GITHUB_OAUTH_TOKEN_URL", "https://github.com/login/oauth/access_token"),
            timeout_seconds=float(os.getenv("GITHUB_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("GITHUB_MAX_RETRIES", "3")),
        )
