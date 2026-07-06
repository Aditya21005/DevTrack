from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["local", "development", "test", "staging", "production"]
LogFormat = Literal["json", "console"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
JWTAlgorithm = Literal["HS256", "HS384", "HS512"]


class Settings(BaseSettings):
    """Runtime configuration for the DevTrack AI backend database layer.

    Values are loaded from environment variables first, then from a local .env
    file for developer machines. Production should inject secrets through the
    deployment platform or a secret manager rather than committing .env files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DEVTRACK_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DevTrack AI"
    environment: Environment = "local"
    debug: bool = False

    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://devtrack:devtrack@localhost:5432/devtrack_ai",
        description="Async-capable PostgreSQL SQLAlchemy URL.",
    )
    database_echo: bool = False
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60, le=86400)
    database_pool_use_lifo: bool = True
    database_statement_timeout_ms: int = Field(default=30000, ge=1000, le=600000)
    database_lock_timeout_ms: int = Field(default=5000, ge=100, le=120000)
    database_application_name: str = "devtrack-ai-api"

    log_level: LogLevel = "INFO"
    log_format: LogFormat = "json"
    log_sql: bool = False

    jwt_access_secret_key: SecretStr = Field(default="dev-only-access-secret-change-me")
    jwt_refresh_secret_key: SecretStr = Field(default="dev-only-refresh-secret-change-me")
    jwt_algorithm: JWTAlgorithm = "HS256"
    jwt_issuer: str = "devtrack-ai"
    jwt_audience: str = "devtrack-ai-api"
    access_token_expires_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expires_days: int = Field(default=30, ge=1, le=365)

    password_min_length: int = Field(default=12, ge=8, le=128)
    password_hash_time_cost: int = Field(default=3, ge=1, le=10)
    password_hash_memory_cost: int = Field(default=65536, ge=8192, le=1048576)
    password_hash_parallelism: int = Field(default=4, ge=1, le=16)

    request_id_header: str = "X-Request-ID"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Accept common PostgreSQL URL forms and normalize for SQLAlchemy async.

        Operators often provide postgresql:// URLs from managed platforms. The
        application standard is postgresql+psycopg:// so SQLAlchemy uses the
        psycopg 3 driver consistently.
        """
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @field_validator("debug")
    @classmethod
    def prevent_debug_in_production(cls, value: bool, info) -> bool:
        environment = info.data.get("environment")
        if environment == "production" and value:
            raise ValueError("DEVTRACK_DEBUG must be false in production")
        return value

    @model_validator(mode="after")
    def validate_auth_secrets(self) -> "Settings":
        access_secret = self.jwt_access_secret_key.get_secret_value()
        refresh_secret = self.jwt_refresh_secret_key.get_secret_value()
        if access_secret == refresh_secret:
            raise ValueError("JWT access and refresh secrets must be different")
        if self.is_production:
            weak_defaults = {
                "dev-only-access-secret-change-me",
                "dev-only-refresh-secret-change-me",
            }
            if access_secret in weak_defaults or refresh_secret in weak_defaults:
                raise ValueError("Production JWT secrets must be provided through environment variables")
            if len(access_secret) < 32 or len(refresh_secret) < 32:
                raise ValueError("Production JWT secrets must be at least 32 characters")
        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        return str(self.database_url)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for FastAPI dependency injection and app startup."""
    return Settings()
