from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any

import httpx

from .config import GitHubConfig

logger = logging.getLogger(__name__)


class GitHubClientError(RuntimeError):
    """Base exception for GitHub client failures."""


class GitHubAPIError(GitHubClientError):
    """Raised when GitHub returns a non-success response."""

    def __init__(self, message: str, *, status_code: int, response: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub rate limits the current token."""

    def __init__(self, message: str, *, reset_at_epoch: int | None = None, retry_after_seconds: int | None = None) -> None:
        super().__init__(message, status_code=429)
        self.reset_at_epoch = reset_at_epoch
        self.retry_after_seconds = retry_after_seconds


class GitHubClient:
    """Async GitHub REST and OAuth client.

    The client is intentionally stateless. Callers pass the access token for each
    API call, which keeps the singleton service safe across organizations/users.
    """

    def __init__(self, config: GitHubConfig) -> None:
        self._config = config

    async def exchange_code(self, *, code: str, code_verifier: str, redirect_uri: str) -> dict[str, Any]:
        payload = {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "DevTrack-AI",
        }

        async with httpx.AsyncClient(timeout=self._config.timeout_seconds) as client:
            response = await client.post(self._config.oauth_token_url, data=payload, headers=headers)

        body = self._parse_json(response)
        if response.status_code >= 400 or body.get("error"):
            raise GitHubAPIError(
                body.get("error_description") or body.get("message") or "GitHub OAuth token exchange failed",
                status_code=response.status_code,
                response=body,
            )
        return body

    async def get_authenticated_user(self, access_token: str) -> dict[str, Any]:
        return await self._request("GET", "/user", access_token=access_token)

    async def list_authenticated_repositories(self, access_token: str) -> list[dict[str, Any]]:
        return await self._paginate(
            "/user/repos",
            access_token=access_token,
            params={
                "affiliation": "owner,collaborator,organization_member",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
            },
        )

    async def list_commits(self, access_token: str, full_name: str, *, since: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": 100}
        if since:
            params["since"] = since
        return await self._paginate(f"/repos/{full_name}/commits", access_token=access_token, params=params)

    async def list_issues(self, access_token: str, full_name: str, *, state: str = "all") -> list[dict[str, Any]]:
        issues = await self._paginate(
            f"/repos/{full_name}/issues",
            access_token=access_token,
            params={"state": state, "per_page": 100},
        )
        return [issue for issue in issues if "pull_request" not in issue]

    async def list_pull_requests(self, access_token: str, full_name: str, *, state: str = "all") -> list[dict[str, Any]]:
        return await self._paginate(
            f"/repos/{full_name}/pulls",
            access_token=access_token,
            params={"state": state, "per_page": 100},
        )

    async def _paginate(
        self,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url: str | None = path
        next_params = dict(params or {})

        while next_url:
            response = await self._request("GET", next_url, access_token=access_token, params=next_params, return_response=True)
            body = self._parse_json(response)
            if not isinstance(body, list):
                raise GitHubAPIError("GitHub pagination response was not a list", status_code=response.status_code)
            items.extend(body)
            next_url = response.links.get("next", {}).get("url")
            next_params = None

        return items

    async def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DevTrack-AI",
        }
        url = path_or_url if path_or_url.startswith("http") else f"{self._config.api_base_url}{path_or_url}"
        retry_statuses = {429, 500, 502, 503, 504}

        async with httpx.AsyncClient(timeout=self._config.timeout_seconds) as client:
            for attempt in range(self._config.max_retries + 1):
                response = await client.request(method, url, headers=headers, params=params, json=json_body)
                if response.status_code < 400:
                    return response if return_response else self._parse_json(response)

                if self._is_rate_limited(response):
                    await self._sleep_before_retry(response, attempt)
                    if attempt >= self._config.max_retries:
                        raise self._rate_limit_error(response)
                    continue

                if response.status_code in retry_statuses and attempt < self._config.max_retries:
                    await self._sleep_before_retry(response, attempt)
                    continue

                body = self._parse_json(response)
                raise GitHubAPIError(
                    body.get("message") if isinstance(body, dict) else "GitHub API request failed",
                    status_code=response.status_code,
                    response=body if isinstance(body, dict) else {},
                )

        raise GitHubClientError("GitHub request retry loop exited unexpectedly")

    @staticmethod
    def _parse_json(response: httpx.Response) -> Any:
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned invalid JSON", status_code=response.status_code) from exc

    @staticmethod
    def _is_rate_limited(response: httpx.Response) -> bool:
        remaining = response.headers.get("X-RateLimit-Remaining")
        return response.status_code in {403, 429} and remaining == "0"

    @staticmethod
    async def _sleep_before_retry(response: httpx.Response, attempt: int) -> None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            await asyncio.sleep(min(int(retry_after), 30))
            return
        await asyncio.sleep(min(2**attempt, 10))

    @staticmethod
    def _rate_limit_error(response: httpx.Response) -> GitHubRateLimitError:
        retry_after = response.headers.get("Retry-After")
        reset_at = response.headers.get("X-RateLimit-Reset")
        return GitHubRateLimitError(
            "GitHub API rate limit exceeded",
            reset_at_epoch=int(reset_at) if reset_at and reset_at.isdigit() else None,
            retry_after_seconds=int(retry_after) if retry_after and retry_after.isdigit() else None,
        )
