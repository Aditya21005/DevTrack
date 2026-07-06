from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from devtrack_ai_db.models import IssueLinkType, IssuePriority

_SAFE_OBJECT_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._!''()/=-]{0,2047}$")
_CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x1f\x7f]")
_ALLOWED_ATTACHMENT_CONTENT_TYPES = {
    "application/json",
    "application/pdf",
    "application/zip",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/csv",
    "text/markdown",
    "text/plain",
}


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    status_id: uuid.UUID
    priority: IssuePriority = IssuePriority.medium
    assignee_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    label_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)
    parent_task_id: uuid.UUID | None = None
    due_at: datetime | None = None
    story_points: float | None = Field(default=None, ge=0, le=999.99)
    percent_complete: int = Field(default=0, ge=0, le=100)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Task title is required")
        return normalized

    @field_validator("assignee_ids", "label_ids")
    @classmethod
    def reject_duplicates(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate IDs are not allowed")
        return value


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10000)
    status_id: uuid.UUID | None = None
    priority: IssuePriority | None = None
    parent_task_id: uuid.UUID | None = None
    due_at: datetime | None = None
    story_points: float | None = Field(default=None, ge=0, le=999.99)
    percent_complete: int | None = Field(default=None, ge=0, le=100)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Task title is required")
        return normalized


class TaskAssignRequest(BaseModel):
    user_id: uuid.UUID


class TaskLabelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Label name is required")
        return normalized


class TaskLabelAttachRequest(BaseModel):
    label_id: uuid.UUID


class TaskCommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=10000)

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Comment body is required")
        return normalized


class TaskAttachmentCreateRequest(BaseModel):
    object_key: str = Field(min_length=1, max_length=2048)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(gt=0, le=104_857_600)
    comment_id: uuid.UUID | None = None

    @field_validator("object_key")
    @classmethod
    def validate_object_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Attachment object key is required")
        if normalized.startswith("/") or ".." in normalized or "\\" in normalized or "://" in normalized:
            raise ValueError("Attachment object key contains an unsafe path")
        if _CONTROL_CHARACTER_RE.search(normalized) or not _SAFE_OBJECT_KEY_RE.fullmatch(normalized):
            raise ValueError("Attachment object key contains unsafe characters")
        return normalized

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized or normalized in {".", ".."}:
            raise ValueError("Attachment file name is required")
        if "/" in normalized or "\\" in normalized or _CONTROL_CHARACTER_RE.search(normalized):
            raise ValueError("Attachment file name must not contain path separators or control characters")
        return normalized

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_ATTACHMENT_CONTENT_TYPES:
            raise ValueError("Attachment content type is not allowed")
        return normalized


class TaskDependencyCreateRequest(BaseModel):
    target_task_id: uuid.UUID
    link_type: IssueLinkType = IssueLinkType.blocks


class TaskStatusUpdateRequest(BaseModel):
    status_id: uuid.UUID


class TaskPriorityUpdateRequest(BaseModel):
    priority: IssuePriority


class TaskProgressUpdateRequest(BaseModel):
    percent_complete: int | None = Field(default=None, ge=0, le=100)
    checklist_total: int | None = Field(default=None, ge=0)
    checklist_completed: int | None = Field(default=None, ge=0)
    is_blocked: bool | None = None
    blocked_reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_checklist(self) -> "TaskProgressUpdateRequest":
        if self.checklist_total is not None and self.checklist_completed is not None:
            if self.checklist_completed > self.checklist_total:
                raise ValueError("Completed checklist count cannot exceed total count")
        if self.is_blocked is False and self.blocked_reason:
            raise ValueError("Blocked reason cannot be set when task is not blocked")
        return self


class TaskLabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str


class TaskAssigneeResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str
    avatar_url: str | None = None


class TaskCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issue_id: uuid.UUID
    author_id: uuid.UUID | None = None
    body: str
    created_at: datetime
    updated_at: datetime


class TaskAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issue_id: uuid.UUID | None = None
    comment_id: uuid.UUID | None = None
    uploaded_by_id: uuid.UUID | None = None
    object_key: str
    file_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class TaskDependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_issue_id: uuid.UUID
    target_issue_id: uuid.UUID
    link_type: IssueLinkType


class TaskProgressResponse(BaseModel):
    percent_complete: int
    checklist_total: int
    checklist_completed: int
    is_blocked: bool
    blocked_reason: str | None = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    issue_number: int
    title: str
    description: str | None = None
    status_id: uuid.UUID
    priority: IssuePriority
    parent_task_id: uuid.UUID | None = None
    due_at: datetime | None = None
    story_points: float | None = None
    progress: TaskProgressResponse
    assignees: list[TaskAssigneeResponse] = Field(default_factory=list)
    labels: list[TaskLabelResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str






