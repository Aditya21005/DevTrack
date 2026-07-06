from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_auth.routes import CurrentUser
from devtrack_ai_db.session import get_db_session, get_transactional_session

from .models import ProjectPriority, ProjectStatus
from .schemas import (
    MessageResponse,
    ProjectCreateRequest,
    ProjectDeadlineUpdateRequest,
    ProjectPriorityUpdateRequest,
    ProjectResponse,
    ProjectStatusUpdateRequest,
    ProjectUpdateRequest,
)
from .services import (
    ProjectConflictError,
    ProjectError,
    ProjectNotFoundError,
    ProjectPermissionError,
    ProjectService,
    ProjectValidationError,
    get_project_service,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["projects"])

DbSession = Annotated[AsyncSession, Depends(get_transactional_session)]
ReadOnlyDbSession = Annotated[AsyncSession, Depends(get_db_session)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


def map_project_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProjectNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ProjectConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ProjectPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ProjectValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, ProjectError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Project operation failed")


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    workspace_id: uuid.UUID,
    payload: ProjectCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    try:
        return await project_service.create_project(session, workspace_id, payload, current_user)
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    project_service: ProjectServiceDep,
    status_filter: Annotated[ProjectStatus | None, Query(alias="status")] = None,
    priority: ProjectPriority | None = None,
) -> list[ProjectResponse]:
    try:
        return await project_service.list_projects(session, workspace_id, current_user, status_filter, priority)
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    try:
        return await project_service.get_project(session, workspace_id, project_id, current_user)
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    try:
        return await project_service.update_project(session, workspace_id, project_id, payload, current_user)
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser,
    session: DbSession,
    project_service: ProjectServiceDep,
) -> MessageResponse:
    try:
        await project_service.delete_project(session, workspace_id, project_id, current_user)
        return MessageResponse(message="Project deleted successfully")
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.patch("/{project_id}/status", response_model=ProjectResponse)
async def update_project_status(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectStatusUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    try:
        return await project_service.update_status(session, workspace_id, project_id, payload, current_user)
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.patch("/{project_id}/deadlines", response_model=ProjectResponse)
async def update_project_deadlines(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectDeadlineUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    try:
        return await project_service.update_deadlines(session, workspace_id, project_id, payload, current_user)
    except Exception as exc:
        raise map_project_error(exc) from exc


@router.patch("/{project_id}/priority", response_model=ProjectResponse)
async def update_project_priority(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectPriorityUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    try:
        return await project_service.update_priority(session, workspace_id, project_id, payload, current_user)
    except Exception as exc:
        raise map_project_error(exc) from exc
