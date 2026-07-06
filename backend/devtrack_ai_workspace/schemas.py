from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
_ROLE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 _-]{1,98}[A-Za-z0-9]$")


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if not _EMAIL_RE.fullmatch(normalized):
        raise ValueError("Invalid email address")
    return normalized


def normalize_slug(value: str) -> str:
    normalized = value.strip().lower()
    if not _SLUG_RE.fullmatch(normalized):
        raise ValueError("Slug must be 3-80 characters using lowercase letters, numbers, and hyphens")
    return normalized


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=3, max_length=80)
    default_timezone: str = Field(default="UTC", min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Workspace name is required")
        return normalized

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        return normalize_slug(value)


class WorkspaceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=3, max_length=80)
    default_timezone: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("Workspace name is required")
        return normalized

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_slug(value)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    default_timezone: str
    created_at: datetime
    updated_at: datetime


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not _ROLE_NAME_RE.fullmatch(normalized):
            raise ValueError("Role name must be 3-100 characters and start with a letter")
        return normalized


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = " ".join(value.strip().split())
        if not _ROLE_NAME_RE.fullmatch(normalized):
            raise ValueError("Role name must be 3-100 characters and start with a letter")
        return normalized


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    is_system: bool
    created_at: datetime
    updated_at: datetime


class InviteMemberRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role_id: uuid.UUID | None = None
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class WorkspaceInvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role_id: uuid.UUID | None = None
    expires_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime



class InviteMemberResponse(BaseModel):
    invitation: WorkspaceInvitationResponse
    invite_token: str
    membership_id: uuid.UUID | None = None

class WorkspaceMemberResponse(BaseModel):
    membership_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    display_name: str
    avatar_url: str | None = None
    role_id: uuid.UUID | None = None
    role_name: str | None = None
    status: str
    joined_at: datetime | None = None
    invited_at: datetime | None = None


class UpdateMemberRoleRequest(BaseModel):
    role_id: uuid.UUID


class MessageResponse(BaseModel):
    message: str

