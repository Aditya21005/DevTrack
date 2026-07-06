from __future__ import annotations

from dataclasses import dataclass

import pytest


class Secret:
    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


@dataclass(frozen=True)
class TestSettings:
    password_hash_time_cost: int = 1
    password_hash_memory_cost: int = 8192
    password_hash_parallelism: int = 1
    password_min_length: int = 8
    jwt_access_secret_key: Secret = Secret("test-access-secret-that-is-long-enough")
    jwt_refresh_secret_key: Secret = Secret("test-refresh-secret-that-is-long-enough")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "devtrack-ai-test"
    jwt_audience: str = "devtrack-ai-users-test"
    access_token_expires_minutes: int = 15
    refresh_token_expires_days: int = 7


@pytest.fixture
def test_settings() -> TestSettings:
    return TestSettings()