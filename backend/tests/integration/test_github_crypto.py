from __future__ import annotations

import pytest

from devtrack_ai_integrations.github.crypto import TokenCipher


pytestmark = pytest.mark.integration


def test_github_token_cipher_round_trips_without_plaintext_storage() -> None:
    cipher = TokenCipher("local-development-token-secret")
    plaintext = "github-access-token"

    encrypted = cipher.encrypt(plaintext)

    assert encrypted != plaintext
    assert cipher.decrypt(encrypted) == plaintext