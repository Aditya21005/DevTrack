from __future__ import annotations

import hashlib
import hmac
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

from devtrack_ai_db.config import Settings, get_settings

TokenType = Literal["access", "refresh"]
_PASSWORD_SYMBOL_RE = re.compile(r"[^A-Za-z0-9]")


class TokenSecurityError(ValueError):
    """Raised when a JWT cannot be trusted."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_password_hasher(settings: Settings | None = None) -> PasswordHasher:
    settings = settings or get_settings()
    return PasswordHasher(
        time_cost=settings.password_hash_time_cost,
        memory_cost=settings.password_hash_memory_cost,
        parallelism=settings.password_hash_parallelism,
    )


def validate_password_strength(password: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if len(password) < settings.password_min_length:
        raise ValueError(f"Password must be at least {settings.password_min_length} characters")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters")
    if any(character.isspace() for character in password):
        raise ValueError("Password must not contain whitespace")
    if not any(character.islower() for character in password):
        raise ValueError("Password must contain a lowercase letter")
    if not any(character.isupper() for character in password):
        raise ValueError("Password must contain an uppercase letter")
    if not any(character.isdigit() for character in password):
        raise ValueError("Password must contain a number")
    if not _PASSWORD_SYMBOL_RE.search(password):
        raise ValueError("Password must contain a symbol")


def hash_password(password: str, settings: Settings | None = None) -> str:
    validate_password_strength(password, settings)
    return create_password_hasher(settings).hash(password)


def verify_password(password: str, password_hash: str, settings: Settings | None = None) -> bool:
    try:
        return create_password_hasher(settings).verify(password_hash, password)
    except (InvalidHash, VerifyMismatchError):
        return False


def password_needs_rehash(password_hash: str, settings: Settings | None = None) -> bool:
    return create_password_hasher(settings).check_needs_rehash(password_hash)


def _jwt_secret(settings: Settings, token_type: TokenType) -> str:
    if token_type == "access":
        return settings.jwt_access_secret_key.get_secret_value()
    return settings.jwt_refresh_secret_key.get_secret_value()


def create_jwt_token(
    *,
    subject: uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    settings: Settings | None = None,
    family_id: uuid.UUID | None = None,
    token_id: uuid.UUID | None = None,
) -> tuple[str, uuid.UUID, datetime]:
    settings = settings or get_settings()
    now = utc_now()
    expires_at = now + expires_delta
    jti = token_id or uuid.uuid4()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "jti": str(jti),
        "typ": token_type,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
    }
    if family_id is not None:
        payload["fam"] = str(family_id)

    token = jwt.encode(
        payload,
        _jwt_secret(settings, token_type),
        algorithm=settings.jwt_algorithm,
    )
    return token, jti, expires_at


def decode_jwt_token(token: str, token_type: TokenType, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(settings, token_type),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "jti", "typ", "iss", "aud", "iat", "nbf", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenSecurityError("Invalid or expired token") from exc

    if payload.get("typ") != token_type:
        raise TokenSecurityError("Invalid token type")
    return payload


def hash_refresh_token(refresh_token: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    digest = hmac.new(
        settings.jwt_refresh_secret_key.get_secret_value().encode("utf-8"),
        refresh_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest

