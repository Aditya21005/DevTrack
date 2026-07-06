from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.config import Settings, get_settings
from devtrack_ai_db.models import User

from .models import RefreshToken, UserCredential
from .schemas import AuthTokenResponse, LoginRequest, RegisterRequest, UserPublic
from .security import (
    TokenSecurityError,
    create_jwt_token,
    decode_jwt_token,
    hash_password,
    hash_refresh_token,
    password_needs_rehash,
    utc_now,
    validate_password_strength,
    verify_password,
)

logger = logging.getLogger(__name__)

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthError(RuntimeError):
    """Base authentication domain error."""


class AuthConflictError(AuthError):
    """Raised when registration conflicts with existing state."""


class InvalidCredentialsError(AuthError):
    """Raised for invalid login or token credentials."""


class AccountLockedError(AuthError):
    """Raised when an account is temporarily locked."""


class InactiveUserError(AuthError):
    """Raised when an inactive user attempts authentication."""


@dataclass(frozen=True)
class ClientContext:
    ip_address: str | None = None
    user_agent: str | None = None


class AuthService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def register(
        self,
        session: AsyncSession,
        payload: RegisterRequest,
        client: ClientContext | None = None,
    ) -> AuthTokenResponse:
        validate_password_strength(payload.password, self.settings)
        existing_user = await self._get_user_by_email(session, payload.email)
        if existing_user is not None:
            raise AuthConflictError("A user with this email already exists")

        now = utc_now()
        user = User(
            email=payload.email,
            display_name=payload.display_name,
            is_active=True,
            preferences={},
        )
        session.add(user)
        await session.flush()

        credential = UserCredential(
            user_id=user.id,
            password_hash=hash_password(payload.password, self.settings),
            password_changed_at=now,
        )
        session.add(credential)
        await session.flush()

        logger.info("auth.user_registered", extra={"user_id": str(user.id)})
        return await self._issue_token_response(session, user, client)

    async def login(
        self,
        session: AsyncSession,
        payload: LoginRequest,
        client: ClientContext | None = None,
    ) -> AuthTokenResponse:
        user = await self._get_user_by_email(session, payload.email)
        credential = await self._get_credential_for_user(session, user.id) if user else None

        if user is None or credential is None:
            raise InvalidCredentialsError("Invalid email or password")
        self._ensure_user_can_authenticate(user)
        self._ensure_account_not_locked(credential)

        if not verify_password(payload.password, credential.password_hash, self.settings):
            await self._record_failed_login(credential)
            raise InvalidCredentialsError("Invalid email or password")

        now = utc_now()
        if password_needs_rehash(credential.password_hash, self.settings):
            credential.password_hash = hash_password(payload.password, self.settings)
            credential.password_changed_at = now

        credential.failed_login_attempts = 0
        credential.locked_until = None
        credential.last_login_at = now
        user.last_login_at = now
        await session.flush()

        logger.info("auth.user_logged_in", extra={"user_id": str(user.id)})
        return await self._issue_token_response(session, user, client)

    async def refresh(
        self,
        session: AsyncSession,
        refresh_token: str,
        client: ClientContext | None = None,
    ) -> AuthTokenResponse:
        payload = self._decode_refresh_payload(refresh_token)
        token_hash = hash_refresh_token(refresh_token, self.settings)
        token_record = await self._get_refresh_token_for_update(session, token_hash)
        now = utc_now()

        if token_record is None:
            raise InvalidCredentialsError("Invalid refresh token")
        if token_record.revoked_at is not None:
            await self._revoke_refresh_family(session, token_record.family_id, client)
            raise InvalidCredentialsError("Refresh token has been revoked")
        if token_record.expires_at <= now:
            token_record.revoked_at = now
            token_record.revoked_by_ip = client.ip_address if client else None
            raise InvalidCredentialsError("Refresh token has expired")
        if str(token_record.user_id) != payload.get("sub"):
            await self._revoke_refresh_family(session, token_record.family_id, client)
            raise InvalidCredentialsError("Invalid refresh token")

        user = await session.get(User, token_record.user_id)
        if user is None:
            raise InvalidCredentialsError("Invalid refresh token")
        self._ensure_user_can_authenticate(user)

        token_record.revoked_at = now
        token_record.revoked_by_ip = client.ip_address if client else None
        response, new_token_record = await self._issue_token_response_with_record(
            session,
            user,
            client,
            family_id=token_record.family_id,
        )
        token_record.replaced_by_token_id = new_token_record.id
        await session.flush()

        logger.info("auth.refresh_rotated", extra={"user_id": str(user.id)})
        return response

    async def logout(
        self,
        session: AsyncSession,
        refresh_token: str,
        client: ClientContext | None = None,
    ) -> None:
        try:
            self._decode_refresh_payload(refresh_token)
        except InvalidCredentialsError:
            return

        token_hash = hash_refresh_token(refresh_token, self.settings)
        token_record = await self._get_refresh_token_for_update(session, token_hash)
        if token_record is None or token_record.revoked_at is not None:
            return

        token_record.revoked_at = utc_now()
        token_record.revoked_by_ip = client.ip_address if client else None
        await session.flush()
        logger.info("auth.user_logged_out", extra={"user_id": str(token_record.user_id)})

    async def get_current_user(self, session: AsyncSession, access_token: str) -> User:
        try:
            payload = decode_jwt_token(access_token, "access", self.settings)
            user_id = uuid.UUID(str(payload["sub"]))
        except (TokenSecurityError, KeyError, ValueError) as exc:
            raise InvalidCredentialsError("Invalid access token") from exc

        user = await session.get(User, user_id)
        if user is None:
            raise InvalidCredentialsError("Invalid access token")
        self._ensure_user_can_authenticate(user)
        return user

    async def _issue_token_response(
        self,
        session: AsyncSession,
        user: User,
        client: ClientContext | None,
        family_id: uuid.UUID | None = None,
    ) -> AuthTokenResponse:
        response, _token_record = await self._issue_token_response_with_record(session, user, client, family_id)
        return response

    async def _issue_token_response_with_record(
        self,
        session: AsyncSession,
        user: User,
        client: ClientContext | None,
        family_id: uuid.UUID | None = None,
    ) -> tuple[AuthTokenResponse, RefreshToken]:
        access_token, _access_jti, _access_expires_at = create_jwt_token(
            subject=user.id,
            token_type="access",
            expires_delta=timedelta(minutes=self.settings.access_token_expires_minutes),
            settings=self.settings,
        )
        family_id = family_id or uuid.uuid4()
        refresh_token, _refresh_jti, refresh_expires_at = create_jwt_token(
            subject=user.id,
            token_type="refresh",
            expires_delta=timedelta(days=self.settings.refresh_token_expires_days),
            settings=self.settings,
            family_id=family_id,
        )
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token, self.settings),
            family_id=family_id,
            expires_at=refresh_expires_at,
            created_by_ip=client.ip_address if client else None,
            user_agent=client.user_agent if client else None,
        )
        session.add(token_record)
        await session.flush()

        response = AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_expires_minutes * 60,
            user=UserPublic.model_validate(user),
        )
        return response, token_record

    async def _get_user_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _get_credential_for_user(self, session: AsyncSession, user_id: uuid.UUID) -> UserCredential | None:
        result = await session.execute(select(UserCredential).where(UserCredential.user_id == user_id))
        return result.scalar_one_or_none()

    async def _get_refresh_token_for_update(self, session: AsyncSession, token_hash: str) -> RefreshToken | None:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        )
        return result.scalar_one_or_none()

    async def _record_failed_login(self, credential: UserCredential) -> None:
        credential.failed_login_attempts += 1
        if credential.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            credential.locked_until = utc_now() + timedelta(minutes=LOCKOUT_MINUTES)
        logger.warning("auth.failed_login", extra={"user_id": str(credential.user_id)})

    async def _revoke_refresh_family(
        self,
        session: AsyncSession,
        family_id: uuid.UUID,
        client: ClientContext | None,
    ) -> None:
        await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(
                revoked_at=utc_now(),
                revoked_by_ip=client.ip_address if client else None,
            )
        )

    def _decode_refresh_payload(self, refresh_token: str) -> dict[str, object]:
        try:
            return decode_jwt_token(refresh_token, "refresh", self.settings)
        except TokenSecurityError as exc:
            raise InvalidCredentialsError("Invalid refresh token") from exc

    def _ensure_user_can_authenticate(self, user: User) -> None:
        if user.deleted_at is not None or not user.is_active:
            raise InactiveUserError("User account is inactive")

    def _ensure_account_not_locked(self, credential: UserCredential) -> None:
        if credential.locked_until is not None and credential.locked_until > utc_now():
            raise AccountLockedError("Account is temporarily locked")


def get_auth_service() -> AuthService:
    return AuthService()
