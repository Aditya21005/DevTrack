from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_auth.routes import CurrentUser
from devtrack_ai_db.session import get_db_session, get_transactional_session

from .schemas import (
    MessageResponse,
    TaskAssignRequest,
    TaskAttachmentCreateRequest,
    TaskAttachmentResponse,
    TaskCommentCreateRequest,
    TaskCommentResponse,
    TaskCreateRequest,
    TaskDependencyCreateRequest,
    TaskDependencyResponse,
    TaskLabelAttachRequest,
    TaskLabelCreateRequest,
    TaskLabelResponse,
    TaskPriorityUpdateRequest,
    TaskProgressUpdateRequest,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from .services import (
    TaskConflictError,
    TaskError,
    TaskNotFoundError,
    TaskPermissionError,
    TaskService,
    TaskValidationError,
    get_task_service,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/projects/{project_id}/tasks", tags=["tasks"])

DbSession = Annotated[AsyncSession, Depends(get_transactional_session)]
ReadOnlyDbSession = Annotated[AsyncSession, Depends(get_db_session)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def map_task_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TaskNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, TaskConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, TaskPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, TaskValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, TaskError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Task operation failed")


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: TaskCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.create_task(session, workspace_id, project_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    task_service: TaskServiceDep,
) -> list[TaskResponse]:
    try:
        return await task_service.list_tasks(session, workspace_id, project_id, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.get_task(session, workspace_id, project_id, task_id, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.update_task(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> MessageResponse:
    try:
        await task_service.delete_task(session, workspace_id, project_id, task_id, current_user)
        return MessageResponse(message="Task deleted successfully")
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.post("/{task_id}/assignees", response_model=TaskResponse)
async def assign_task(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskAssignRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.assign_task(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.post("/labels", response_model=TaskLabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: TaskLabelCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskLabelResponse:
    try:
        return await task_service.create_label(session, workspace_id, project_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.post("/{task_id}/labels", response_model=TaskResponse)
async def attach_label(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskLabelAttachRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.attach_label(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskCommentCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskCommentResponse:
    try:
        return await task_service.add_comment(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.get("/{task_id}/comments", response_model=list[TaskCommentResponse])
async def list_comments(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    task_service: TaskServiceDep,
) -> list[TaskCommentResponse]:
    try:
        return await task_service.list_comments(session, workspace_id, project_id, task_id, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.post("/{task_id}/attachments", response_model=TaskAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def add_attachment(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskAttachmentCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskAttachmentResponse:
    try:
        return await task_service.add_attachment(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.get("/{task_id}/attachments", response_model=list[TaskAttachmentResponse])
async def list_attachments(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    task_service: TaskServiceDep,
) -> list[TaskAttachmentResponse]:
    try:
        return await task_service.list_attachments(session, workspace_id, project_id, task_id, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.post("/{task_id}/dependencies", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
async def add_dependency(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskDependencyCreateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskDependencyResponse:
    try:
        return await task_service.add_dependency(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.get("/{task_id}/dependencies", response_model=list[TaskDependencyResponse])
async def list_dependencies(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    task_service: TaskServiceDep,
) -> list[TaskDependencyResponse]:
    try:
        return await task_service.list_dependencies(session, workspace_id, project_id, task_id, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_status(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskStatusUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.update_status(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.patch("/{task_id}/priority", response_model=TaskResponse)
async def update_priority(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskPriorityUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.update_priority(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc


@router.patch("/{task_id}/progress", response_model=TaskResponse)
async def update_progress(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskProgressUpdateRequest,
    current_user: CurrentUser,
    session: DbSession,
    task_service: TaskServiceDep,
) -> TaskResponse:
    try:
        return await task_service.update_progress(session, workspace_id, project_id, task_id, payload, current_user)
    except Exception as exc:
        raise map_task_error(exc) from exc
