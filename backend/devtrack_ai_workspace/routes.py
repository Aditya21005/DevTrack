from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_auth.routes import CurrentUser
from devtrack_ai_db.models import User
from devtrack_ai_db.session import get_db_session, get_transactional_session

from .schemas import (
    InviteMemberRequest,
    InviteMemberResponse,
    MessageResponse,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
    UpdateMemberRoleRequest,
    WorkspaceCreateRequest,
    WorkspaceInvitationResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from .services import (
    WorkspaceConflictError,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspacePermissionError,
    WorkspaceService,
    WorkspaceValidationError,
    get_workspace_service,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

DbSession = Annotated[AsyncSession, Depends(get_transactional_session)]
ReadOnlyDbSession = Annotated[AsyncSession, Depends(get_db_session)]
WorkspaceServiceDep = Annotated[WorkspaceService, Depends(get_workspace_service)]


def map_workspace_error(exc: Exception) -> HTTPException:
    if isinstance(exc, WorkspaceNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, WorkspaceConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, WorkspacePermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, WorkspaceValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, WorkspaceError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Workspace operation failed")


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    try:
        workspace = await workspace_service.create_workspace(session, payload, current_user)
        return WorkspaceResponse.model_validate(workspace)
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    try:
        workspace = await workspace_service.update_workspace(session, workspace_id, payload, current_user)
        return WorkspaceResponse.model_validate(workspace)
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.delete("/{workspace_id}", response_model=MessageResponse)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> MessageResponse:
    try:
        await workspace_service.delete_workspace(session, workspace_id, current_user)
        return MessageResponse(message="Workspace deleted successfully")
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.post("/{workspace_id}/invites", response_model=InviteMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    workspace_id: uuid.UUID,
    payload: InviteMemberRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> InviteMemberResponse:
    try:
        result = await workspace_service.invite_member(session, workspace_id, payload, current_user)
        return InviteMemberResponse(
            invitation=WorkspaceInvitationResponse.model_validate(result.invitation),
            invite_token=result.invite_token,
            membership_id=result.membership.id if result.membership else None,
        )
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    workspace_service: WorkspaceServiceDep,
) -> list[WorkspaceMemberResponse]:
    try:
        return await workspace_service.list_members(session, workspace_id, current_user)
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.patch("/{workspace_id}/members/{membership_id}/role", response_model=MessageResponse)
async def update_member_role(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> MessageResponse:
    try:
        await workspace_service.update_member_role(session, workspace_id, membership_id, payload, current_user)
        return MessageResponse(message="Member role updated successfully")
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.get("/{workspace_id}/roles", response_model=list[RoleResponse])
async def list_roles(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    workspace_service: WorkspaceServiceDep,
) -> list[RoleResponse]:
    try:
        roles = await workspace_service.list_roles(session, workspace_id, current_user)
        return [RoleResponse.model_validate(role) for role in roles]
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.post("/{workspace_id}/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    workspace_id: uuid.UUID,
    payload: RoleCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> RoleResponse:
    try:
        role = await workspace_service.create_role(session, workspace_id, payload, current_user)
        return RoleResponse.model_validate(role)
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.patch("/{workspace_id}/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    payload: RoleUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> RoleResponse:
    try:
        role = await workspace_service.update_role(session, workspace_id, role_id, payload, current_user)
        return RoleResponse.model_validate(role)
    except Exception as exc:
        raise map_workspace_error(exc) from exc


@router.delete("/{workspace_id}/roles/{role_id}", response_model=MessageResponse)
async def delete_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: CurrentUser,
    session: DbSession,
    workspace_service: WorkspaceServiceDep,
) -> MessageResponse:
    try:
        await workspace_service.delete_role(session, workspace_id, role_id, current_user)
        return MessageResponse(message="Role deleted successfully")
    except Exception as exc:
        raise map_workspace_error(exc) from exc
