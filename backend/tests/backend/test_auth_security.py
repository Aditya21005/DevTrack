from __future__ import annotations

from datetime import timedelta
import uuid

import pytest

from devtrack_ai_auth.security import (
    TokenSecurityError,
    create_jwt_token,
    decode_jwt_token,
    hash_refresh_token,
    validate_password_strength,
)


pytestmark = pytest.mark.auth


def test_password_strength_rejects_weak_password(test_settings) -> None:
    with pytest.raises(ValueError):
        validate_password_strength("password", test_settings)


def test_access_token_round_trip_contains_expected_claims(test_settings) -> None:
    user_id = uuid.uuid4()

    token, token_id, expires_at = create_jwt_token(
        subject=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=5),
        settings=test_settings,
    )

    payload = decode_jwt_token(token, "access", test_settings)

    assert payload["sub"] == str(user_id)
    assert payload["jti"] == str(token_id)
    assert payload["typ"] == "access"
    assert expires_at.isoformat()


def test_refresh_token_cannot_be_used_as_access_token(test_settings) -> None:
    token, _token_id, _expires_at = create_jwt_token(
        subject=uuid.uuid4(),
        token_type="refresh",
        expires_delta=timedelta(days=1),
        settings=test_settings,
        family_id=uuid.uuid4(),
    )

    with pytest.raises(TokenSecurityError):
        decode_jwt_token(token, "access", test_settings)


def test_refresh_token_hash_is_stable_and_secret_bound(test_settings) -> None:
    refresh_token = "refresh-token-value"

    first = hash_refresh_token(refresh_token, test_settings)
    second = hash_refresh_token(refresh_token, test_settings)

    assert first == second
    assert first != refresh_token
    assert len(first) == 64