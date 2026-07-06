from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import ProjectPriority, ProjectStatus

ProjectVisibilityValue = Literal["private", "organization"]
_PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,19}$")


def normalize_project_key(value: str) -> str:
    normalized = value.strip().upper().replace("-", "_")
    if not _PROJECT_KEY_RE.fullmatch(normalized):
        raise ValueError("Project key must be 2-20 characters using uppercase letters, numbers, or underscores")
    return normalized


def normalize_name(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError("Project name is required")
    return normalized


class ProjectCreateRequest(BaseModel):
    key: str = Field(min_length=2, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    visibility: ProjectVisibilityValue = "organization"
    status: ProjectStatus = ProjectStatus.planned
    priority: ProjectPriority = ProjectPriority.medium
    starts_at: datetime | None = None
    due_at: datetime | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return normalize_project_key(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_name(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectCreateRequest":
        if self.starts_at and self.due_at and self.starts_at > self.due_at:
            raise ValueError("Project start date cannot be after due date")
        return self


class ProjectUpdateRequest(BaseModel):
    key: str | None = Field(default=None, min_length=2, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    visibility: ProjectVisibilityValue | None = None
    status: ProjectStatus | None = None
    priority: ProjectPriority | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_project_key(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_name(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectUpdateRequest":
        if self.starts_at and self.due_at and self.starts_at > self.due_at:
            raise ValueError("Project start date cannot be after due date")
        return self


class ProjectStatusUpdateRequest(BaseModel):
    status: ProjectStatus


class ProjectDeadlineUpdateRequest(BaseModel):
    starts_at: datetime | None = None
    due_at: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectDeadlineUpdateRequest":
        if self.starts_at and self.due_at and self.starts_at > self.due_at:
            raise ValueError("Project start date cannot be after due date")
        return self


class ProjectPriorityUpdateRequest(BaseModel):
    priority: ProjectPriority


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    visibility: str
    status: ProjectStatus
    priority: ProjectPriority
    starts_at: datetime | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
