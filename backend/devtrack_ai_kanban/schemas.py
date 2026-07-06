from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import KanbanEventType


class KanbanTaskCard(BaseModel):
    id: uuid.UUID
    issue_number: int
    title: str
    priority: str
    rank: str
    status_id: uuid.UUID
    assignee_ids: list[uuid.UUID] = Field(default_factory=list)
    due_at: datetime | None = None
    updated_at: datetime


class KanbanColumnResponse(BaseModel):
    id: uuid.UUID
    name: str
    workflow_status_id: uuid.UUID
    position: int
    wip_limit: int | None = None
    tasks: list[KanbanTaskCard] = Field(default_factory=list)


class KanbanBoardResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    is_default: bool
    columns: list[KanbanColumnResponse]


class MoveTaskRequest(BaseModel):
    task_id: uuid.UUID
    target_column_id: uuid.UUID
    before_task_id: uuid.UUID | None = None
    after_task_id: uuid.UUID | None = None
    client_event_id: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def validate_neighbor_window(self) -> "MoveTaskRequest":
        if self.before_task_id is not None and self.before_task_id == self.task_id:
            raise ValueError("before_task_id cannot equal task_id")
        if self.after_task_id is not None and self.after_task_id == self.task_id:
            raise ValueError("after_task_id cannot equal task_id")
        if self.before_task_id is not None and self.after_task_id is not None and self.before_task_id == self.after_task_id:
            raise ValueError("before_task_id and after_task_id cannot be the same")
        return self


class UpdateTaskStatusRequest(BaseModel):
    task_id: uuid.UUID
    target_column_id: uuid.UUID
    client_event_id: str | None = Field(default=None, min_length=1, max_length=120)


class KanbanMutationResponse(BaseModel):
    task: KanbanTaskCard
    event_id: uuid.UUID
    event_type: KanbanEventType
    board_version: int


class KanbanEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    board_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    event_type: KanbanEventType
    payload: dict
    event_key: str
    created_at: datetime
    processed_at: datetime | None = None
