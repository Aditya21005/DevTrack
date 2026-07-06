from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request, status
from fastapi.responses import JSONResponse


class RateLimitExceededError(RuntimeError):
    """Raised when a client exceeds a configured request budget."""


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    max_requests: int
    window_seconds: int


class InMemoryRateLimiter:
    """Process-local sliding-window limiter for sensitive endpoints.

    This prevents trivial credential stuffing on a single API worker. In a
    horizontally scaled deployment, replace this with the same interface backed
    by Redis or another shared low-latency store.
    """

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, *, key: str, rule: RateLimitRule) -> None:
        now = time.monotonic()
        cutoff = now - rule.window_seconds
        bucket_key = (rule.name, key)

        with self._lock:
            bucket = self._events[bucket_key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= rule.max_requests:
                raise RateLimitExceededError("Too many requests")
            bucket.append(now)


rate_limiter = InMemoryRateLimiter()
AUTH_RATE_LIMIT = RateLimitRule(name="auth", max_requests=20, window_seconds=60)


def client_rate_limit_key(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:120]
    return f"{client_host}:{user_agent}"


async def rate_limit_auth(request: Request) -> None:
    rate_limiter.check(key=client_rate_limit_key(request), rule=AUTH_RATE_LIMIT)


async def rate_limit_exception_handler(_request: Request, _exc: RateLimitExceededError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please try again later."},
        headers={"Retry-After": str(AUTH_RATE_LIMIT.window_seconds)},
    )

