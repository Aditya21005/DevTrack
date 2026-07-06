from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from devtrack_ai_db.access_control import (
    ADMIN_ROLE_NAME,
    MEMBER_ROLE_NAME,
    OWNER_ROLE_NAME,
    has_admin_role,
    has_owner_role,
)
from devtrack_ai_db.config import Settings, get_settings
from devtrack_ai_db.models import Membership, MembershipStatus, Organization, Role, User

from .models import WorkspaceInvitation
from .schemas import (
    InviteMemberRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
    UpdateMemberRoleRequest,
    WorkspaceCreateRequest,
    WorkspaceMemberResponse,
    WorkspaceUpdateRequest,
)

logger = logging.getLogger(__name__)

DEFAULT_INVITE_EXPIRY_DAYS = 7


class WorkspaceError(RuntimeError):
    """Base workspace domain error."""


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace does not exist or is unavailable."""


class WorkspaceConflictError(WorkspaceError):
    """Raised when a workspace operation conflicts with existing data."""


class WorkspacePermissionError(WorkspaceError):
    """Raised when the actor lacks workspace permissions."""


class WorkspaceValidationError(WorkspaceError):
    """Raised when a workspace operation violates business rules."""


@dataclass(frozen=True)
class InvitationResult:
    invitation: WorkspaceInvitation
    invite_token: str
    membership: Membership | None


class WorkspaceService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def create_workspace(
        self,
        session: AsyncSession,
        payload: WorkspaceCreateRequest,
        actor: User,
    ) -> Organization:
        await self._ensure_slug_available(session, payload.slug)

        workspace = Organization(
            slug=payload.slug,
            name=payload.name,
            default_timezone=payload.default_timezone,
            settings={},
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        session.add(workspace)
        await session.flush()

        owner_role, admin_role, member_role = await self._create_default_roles(session, workspace.id, actor.id)
        membership = Membership(
            organization_id=workspace.id,
            user_id=actor.id,
            role_id=owner_role.id,
            status=MembershipStatus.active,
            joined_at=self._now(),
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        session.add(membership)
        await session.flush()

        logger.info(
            "workspace.created",
            extra={
                "workspace_id": str(workspace.id),
                "actor_id": str(actor.id),
                "default_role_ids": [str(owner_role.id), str(admin_role.id), str(member_role.id)],
            },
        )
        return workspace

    async def update_workspace(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        payload: WorkspaceUpdateRequest,
        actor: User,
    ) -> Organization:
        workspace = await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)

        if payload.slug is not None and payload.slug != workspace.slug:
            await self._ensure_slug_available(session, payload.slug, exclude_workspace_id=workspace_id)
            workspace.slug = payload.slug
        if payload.name is not None:
            workspace.name = payload.name
        if payload.default_timezone is not None:
            workspace.default_timezone = payload.default_timezone
        workspace.updated_by_id = actor.id
        workspace.version += 1
        await session.flush()

        logger.info("workspace.updated", extra={"workspace_id": str(workspace_id), "actor_id": str(actor.id)})
        return workspace

    async def delete_workspace(self, session: AsyncSession, workspace_id: uuid.UUID, actor: User) -> None:
        workspace = await self._get_workspace_required(session, workspace_id)
        await self._require_owner(session, workspace_id, actor.id)

        now = self._now()
        workspace.deleted_at = now
        workspace.deleted_by_id = actor.id
        workspace.updated_by_id = actor.id
        workspace.version += 1
        await session.flush()

        logger.info("workspace.deleted", extra={"workspace_id": str(workspace_id), "actor_id": str(actor.id)})

    async def invite_member(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        payload: InviteMemberRequest,
        actor: User,
    ) -> InvitationResult:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)
        role = await self._get_role_required(session, workspace_id, payload.role_id) if payload.role_id else await self._get_default_member_role(session, workspace_id)

        existing_user = await self._get_user_by_email(session, payload.email)
        membership: Membership | None = None
        if existing_user is not None:
            membership = await self._upsert_invited_membership(session, workspace_id, existing_user.id, role.id, actor.id)

        invitation_token = secrets.token_urlsafe(32)
        invitation = WorkspaceInvitation(
            organization_id=workspace_id,
            email=payload.email,
            role_id=role.id,
            token_hash=self._hash_invitation_token(invitation_token),
            expires_at=self._now() + timedelta(days=DEFAULT_INVITE_EXPIRY_DAYS),
            message=payload.message,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        session.add(invitation)
        await session.flush()

        logger.info(
            "workspace.member_invited",
            extra={"workspace_id": str(workspace_id), "actor_id": str(actor.id), "invitee_email": payload.email},
        )
        return InvitationResult(invitation=invitation, invite_token=invitation_token, membership=membership)

    async def list_members(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        actor: User,
    ) -> list[WorkspaceMemberResponse]:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)

        result = await session.execute(
            select(Membership, User, Role)
            .join(User, Membership.user_id == User.id)
            .outerjoin(Role, Membership.role_id == Role.id)
            .where(
                Membership.organization_id == workspace_id,
                Membership.deleted_at.is_(None),
                User.deleted_at.is_(None),
            )
            .order_by(User.display_name.asc(), User.email.asc())
        )

        members: list[WorkspaceMemberResponse] = []
        for membership, user, role in result.all():
            members.append(
                WorkspaceMemberResponse(
                    membership_id=membership.id,
                    user_id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    avatar_url=user.avatar_url,
                    role_id=role.id if role else None,
                    role_name=role.name if role else None,
                    status=membership.status.value,
                    joined_at=membership.joined_at,
                    invited_at=membership.invited_at,
                )
            )
        return members

    async def list_roles(self, session: AsyncSession, workspace_id: uuid.UUID, actor: User) -> list[Role]:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)
        result = await session.execute(
            select(Role)
            .where(Role.organization_id == workspace_id, Role.deleted_at.is_(None))
            .order_by(Role.is_system.desc(), Role.name.asc())
        )
        return list(result.scalars().all())

    async def create_role(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        payload: RoleCreateRequest,
        actor: User,
    ) -> Role:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)
        await self._ensure_role_name_available(session, workspace_id, payload.name)

        role = Role(
            organization_id=workspace_id,
            name=payload.name,
            description=payload.description,
            is_system=False,
            created_by_id=actor.id,
            updated_by_id=actor.id,
        )
        session.add(role)
        await session.flush()
        logger.info("workspace.role_created", extra={"workspace_id": str(workspace_id), "role_id": str(role.id)})
        return role

    async def update_role(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        role_id: uuid.UUID,
        payload: RoleUpdateRequest,
        actor: User,
    ) -> Role:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)
        role = await self._get_role_required(session, workspace_id, role_id)

        if role.is_system and payload.name is not None and payload.name.lower() != role.name.lower():
            raise WorkspaceValidationError("System role names cannot be changed")
        if payload.name is not None and payload.name.lower() != role.name.lower():
            await self._ensure_role_name_available(session, workspace_id, payload.name, exclude_role_id=role_id)
            role.name = payload.name
        if payload.description is not None:
            role.description = payload.description
        role.updated_by_id = actor.id
        role.version += 1
        await session.flush()
        logger.info("workspace.role_updated", extra={"workspace_id": str(workspace_id), "role_id": str(role.id)})
        return role

    async def delete_role(self, session: AsyncSession, workspace_id: uuid.UUID, role_id: uuid.UUID, actor: User) -> None:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)
        role = await self._get_role_required(session, workspace_id, role_id)
        if role.is_system:
            raise WorkspaceValidationError("System roles cannot be deleted")

        assigned_count = await self._count_active_members_with_role(session, workspace_id, role_id)
        if assigned_count > 0:
            raise WorkspaceConflictError("Role is assigned to active members")

        role.deleted_at = self._now()
        role.deleted_by_id = actor.id
        role.updated_by_id = actor.id
        role.version += 1
        await session.flush()
        logger.info("workspace.role_deleted", extra={"workspace_id": str(workspace_id), "role_id": str(role_id)})

    async def update_member_role(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        payload: UpdateMemberRoleRequest,
        actor: User,
    ) -> Membership:
        await self._get_workspace_required(session, workspace_id)
        await self._require_admin(session, workspace_id, actor.id)
        membership = await self._get_membership_required(session, workspace_id, membership_id)
        new_role = await self._get_role_required(session, workspace_id, payload.role_id)
        current_role = await self._get_role_by_id(session, membership.role_id) if membership.role_id else None

        if current_role and current_role.name.lower() == OWNER_ROLE_NAME and new_role.name.lower() != OWNER_ROLE_NAME:
            await self._ensure_not_last_owner(session, workspace_id, membership.id)

        membership.role_id = new_role.id
        membership.updated_by_id = actor.id
        membership.version += 1
        await session.flush()
        logger.info(
            "workspace.member_role_updated",
            extra={"workspace_id": str(workspace_id), "membership_id": str(membership_id), "role_id": str(new_role.id)},
        )
        return membership

    async def _create_default_roles(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> tuple[Role, Role, Role]:
        roles = [
            Role(
                organization_id=workspace_id,
                name=OWNER_ROLE_NAME.title(),
                description="Full workspace control, including deletion and ownership management.",
                is_system=True,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            ),
            Role(
                organization_id=workspace_id,
                name=ADMIN_ROLE_NAME.title(),
                description="Manage workspace settings, members, invitations, and roles.",
                is_system=True,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            ),
            Role(
                organization_id=workspace_id,
                name=MEMBER_ROLE_NAME.title(),
                description="Standard workspace access.",
                is_system=True,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            ),
        ]
        session.add_all(roles)
        await session.flush()
        return roles[0], roles[1], roles[2]

    async def _upsert_invited_membership(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> Membership:
        result = await session.execute(
            select(Membership)
            .where(Membership.organization_id == workspace_id, Membership.user_id == user_id)
            .with_for_update()
        )
        membership = result.scalar_one_or_none()
        now = self._now()
        if membership is None:
            membership = Membership(
                organization_id=workspace_id,
                user_id=user_id,
                role_id=role_id,
                status=MembershipStatus.invited,
                invited_at=now,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
            session.add(membership)
        elif membership.deleted_at is not None:
            membership.deleted_at = None
            membership.deleted_by_id = None
            membership.role_id = role_id
            membership.status = MembershipStatus.invited
            membership.invited_at = now
            membership.updated_by_id = actor_id
            membership.version += 1
        elif membership.status == MembershipStatus.active:
            raise WorkspaceConflictError("User is already an active workspace member")
        else:
            membership.role_id = role_id
            membership.status = MembershipStatus.invited
            membership.invited_at = now
            membership.updated_by_id = actor_id
            membership.version += 1
        await session.flush()
        return membership

    async def _get_workspace_required(self, session: AsyncSession, workspace_id: uuid.UUID) -> Organization:
        workspace = await session.get(Organization, workspace_id)
        if workspace is None or workspace.deleted_at is not None:
            raise WorkspaceNotFoundError("Workspace not found")
        return workspace

    async def _get_membership_required(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
    ) -> Membership:
        result = await session.execute(
            select(Membership)
            .where(
                Membership.id == membership_id,
                Membership.organization_id == workspace_id,
                Membership.deleted_at.is_(None),
            )
            .with_for_update()
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise WorkspaceNotFoundError("Workspace member not found")
        return membership

    async def _get_actor_membership(self, session: AsyncSession, workspace_id: uuid.UUID, actor_id: uuid.UUID) -> Membership:
        result = await session.execute(
            select(Membership)
            .where(
                Membership.organization_id == workspace_id,
                Membership.user_id == actor_id,
                Membership.status == MembershipStatus.active,
                Membership.deleted_at.is_(None),
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise WorkspacePermissionError("Workspace access denied")
        return membership

    async def _require_admin(self, session: AsyncSession, workspace_id: uuid.UUID, actor_id: uuid.UUID) -> Membership:
        membership = await self._get_actor_membership(session, workspace_id, actor_id)
        role = await self._get_role_by_id(session, membership.role_id) if membership.role_id else None
        if not has_admin_role(role):
            raise WorkspacePermissionError("Workspace admin permission required")
        return membership

    async def _require_owner(self, session: AsyncSession, workspace_id: uuid.UUID, actor_id: uuid.UUID) -> Membership:
        membership = await self._get_actor_membership(session, workspace_id, actor_id)
        role = await self._get_role_by_id(session, membership.role_id) if membership.role_id else None
        if not has_owner_role(role):
            raise WorkspacePermissionError("Workspace owner permission required")
        return membership

    async def _get_role_required(self, session: AsyncSession, workspace_id: uuid.UUID, role_id: uuid.UUID) -> Role:
        result = await session.execute(
            select(Role).where(Role.id == role_id, Role.organization_id == workspace_id, Role.deleted_at.is_(None))
        )
        role = result.scalar_one_or_none()
        if role is None:
            raise WorkspaceNotFoundError("Workspace role not found")
        return role

    async def _get_role_by_id(self, session: AsyncSession, role_id: uuid.UUID | None) -> Role | None:
        if role_id is None:
            return None
        return await session.get(Role, role_id)

    async def _get_default_member_role(self, session: AsyncSession, workspace_id: uuid.UUID) -> Role:
        result = await session.execute(
            select(Role).where(
                Role.organization_id == workspace_id,
                func.lower(Role.name) == MEMBER_ROLE_NAME,
                Role.deleted_at.is_(None),
            )
        )
        role = result.scalar_one_or_none()
        if role is None:
            raise WorkspaceValidationError("Default member role is missing")
        return role

    async def _get_user_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def _ensure_slug_available(
        self,
        session: AsyncSession,
        slug: str,
        exclude_workspace_id: uuid.UUID | None = None,
    ) -> None:
        query = select(Organization.id).where(Organization.slug == slug, Organization.deleted_at.is_(None))
        if exclude_workspace_id is not None:
            query = query.where(Organization.id != exclude_workspace_id)
        result = await session.execute(query)
        if result.scalar_one_or_none() is not None:
            raise WorkspaceConflictError("Workspace slug is already in use")

    async def _ensure_role_name_available(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        name: str,
        exclude_role_id: uuid.UUID | None = None,
    ) -> None:
        query = select(Role.id).where(
            Role.organization_id == workspace_id,
            func.lower(Role.name) == name.lower(),
            Role.deleted_at.is_(None),
        )
        if exclude_role_id is not None:
            query = query.where(Role.id != exclude_role_id)
        result = await session.execute(query)
        if result.scalar_one_or_none() is not None:
            raise WorkspaceConflictError("Role name is already in use")

    async def _count_active_members_with_role(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> int:
        result = await session.execute(
            select(func.count(Membership.id)).where(
                Membership.organization_id == workspace_id,
                Membership.role_id == role_id,
                Membership.status == MembershipStatus.active,
                Membership.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def _ensure_not_last_owner(
        self,
        session: AsyncSession,
        workspace_id: uuid.UUID,
        excluded_membership_id: uuid.UUID,
    ) -> None:
        result = await session.execute(
            select(func.count(Membership.id))
            .join(Role, Membership.role_id == Role.id)
            .where(
                Membership.organization_id == workspace_id,
                Membership.id != excluded_membership_id,
                Membership.status == MembershipStatus.active,
                Membership.deleted_at.is_(None),
                Role.deleted_at.is_(None),
                func.lower(Role.name) == OWNER_ROLE_NAME,
            )
        )
        if int(result.scalar_one()) == 0:
            raise WorkspaceValidationError("Workspace must keep at least one active owner")

    def _hash_invitation_token(self, token: str) -> str:
        return hmac.new(
            self.settings.jwt_refresh_secret_key.get_secret_value().encode("utf-8"),
            token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _now(self) -> datetime:
        return datetime.now(UTC)


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()





