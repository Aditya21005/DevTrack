from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_api.rate_limit import rate_limit_auth
from devtrack_ai_db.models import User
from devtrack_ai_db.session import get_db_session, get_transactional_session

from .schemas import AuthTokenResponse, LoginRequest, LogoutRequest, MessageResponse, RefreshTokenRequest, RegisterRequest, UserPublic
from .services import (
    AccountLockedError,
    AuthConflictError,
    AuthService,
    ClientContext,
    InactiveUserError,
    InvalidCredentialsError,
    get_auth_service,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_transactional_session)]
ReadOnlyDbSession = Annotated[AsyncSession, Depends(get_db_session)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_client_context(request: Request) -> ClientContext:
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ClientContext(ip_address=client_host, user_agent=user_agent)


def credentials_exception(message: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def map_auth_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AuthConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, AccountLockedError):
        return HTTPException(status_code=423, detail=str(exc))
    if isinstance(exc, InactiveUserError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, InvalidCredentialsError):
        return credentials_exception(str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication failed")


async def get_current_user(
    credentials: BearerCredentials,
    session: ReadOnlyDbSession,
    auth_service: AuthServiceDep,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception()

    try:
        return await auth_service.get_current_user(session, credentials.credentials)
    except (InvalidCredentialsError, InactiveUserError) as exc:
        raise map_auth_error(exc) from exc


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_auth)])
async def register(
    payload: RegisterRequest,
    request: Request,
    session: DbSession,
    auth_service: AuthServiceDep,
) -> AuthTokenResponse:
    try:
        return await auth_service.register(session, payload, get_client_context(request))
    except Exception as exc:
        raise map_auth_error(exc) from exc


@router.post("/login", response_model=AuthTokenResponse, dependencies=[Depends(rate_limit_auth)])
async def login(
    payload: LoginRequest,
    request: Request,
    session: DbSession,
    auth_service: AuthServiceDep,
) -> AuthTokenResponse:
    try:
        return await auth_service.login(session, payload, get_client_context(request))
    except Exception as exc:
        raise map_auth_error(exc) from exc


@router.post("/refresh", response_model=AuthTokenResponse, dependencies=[Depends(rate_limit_auth)])
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    session: DbSession,
    auth_service: AuthServiceDep,
) -> AuthTokenResponse:
    try:
        return await auth_service.refresh(session, payload.refresh_token, get_client_context(request))
    except Exception as exc:
        raise map_auth_error(exc) from exc


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest,
    request: Request,
    session: DbSession,
    auth_service: AuthServiceDep,
) -> MessageResponse:
    await auth_service.logout(session, payload.refresh_token, get_client_context(request))
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.get("/protected", response_model=MessageResponse)
async def protected_route(current_user: CurrentUser) -> MessageResponse:
    return MessageResponse(message=f"Authenticated as {current_user.email}")


