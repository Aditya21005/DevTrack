from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_auth.routes import CurrentUser
from devtrack_ai_db.session import get_db_session, get_transactional_session

from .schemas import KanbanBoardResponse, KanbanMutationResponse, MoveTaskRequest, UpdateTaskStatusRequest
from .services import (
    KanbanConflictError,
    KanbanError,
    KanbanNotFoundError,
    KanbanPermissionError,
    KanbanService,
    KanbanValidationError,
    get_kanban_service,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/boards", tags=["kanban"])

DbSession = Annotated[AsyncSession, Depends(get_transactional_session)]
ReadOnlyDbSession = Annotated[AsyncSession, Depends(get_db_session)]
KanbanServiceDep = Annotated[KanbanService, Depends(get_kanban_service)]


def map_kanban_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KanbanNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, KanbanConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, KanbanPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, KanbanValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, KanbanError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Kanban operation failed")


@router.get("/{board_id}/kanban", response_model=KanbanBoardResponse)
async def get_kanban_board(
    workspace_id: uuid.UUID,
    board_id: uuid.UUID,
    current_user: CurrentUser,
    session: ReadOnlyDbSession,
    kanban_service: KanbanServiceDep,
) -> KanbanBoardResponse:
    try:
        return await kanban_service.get_board(session, workspace_id, board_id, current_user)
    except Exception as exc:
        raise map_kanban_error(exc) from exc


@router.post("/{board_id}/kanban/move", response_model=KanbanMutationResponse)
async def move_task(
    workspace_id: uuid.UUID,
    board_id: uuid.UUID,
    payload: MoveTaskRequest,
    current_user: CurrentUser,
    session: DbSession,
    kanban_service: KanbanServiceDep,
) -> KanbanMutationResponse:
    try:
        return await kanban_service.move_task(session, workspace_id, board_id, payload, current_user)
    except Exception as exc:
        raise map_kanban_error(exc) from exc


@router.patch("/{board_id}/kanban/status", response_model=KanbanMutationResponse)
async def update_task_status(
    workspace_id: uuid.UUID,
    board_id: uuid.UUID,
    payload: UpdateTaskStatusRequest,
    current_user: CurrentUser,
    session: DbSession,
    kanban_service: KanbanServiceDep,
) -> KanbanMutationResponse:
    try:
        return await kanban_service.update_status(session, workspace_id, board_id, payload, current_user)
    except Exception as exc:
        raise map_kanban_error(exc) from exc
