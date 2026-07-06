from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class TokenCryptoError(RuntimeError):
    """Raised when GitHub token encryption or decryption fails."""


class TokenCipher:
    def __init__(self, secret: str) -> None:
        if not secret:
            raise TokenCryptoError("Token encryption secret is required")
        self._fernet = Fernet(self._normalize_key(secret))

    def encrypt(self, value: str) -> str:
        if not value:
            raise TokenCryptoError("Cannot encrypt an empty token")
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise TokenCryptoError("Stored GitHub token could not be decrypted") from exc

    def _normalize_key(self, secret: str) -> bytes:
        candidate = secret.encode("utf-8")
        try:
            Fernet(candidate)
            return candidate
        except Exception:
            digest = hashlib.sha256(candidate).digest()
            return base64.urlsafe_b64encode(digest)
