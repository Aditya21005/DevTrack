from __future__ import annotations

from typing import Iterable, TypeAlias

from devtrack_ai_db.models import Membership, MembershipStatus, Role

OWNER_ROLE_NAME = "owner"
ADMIN_ROLE_NAME = "admin"
MEMBER_ROLE_NAME = "member"
ADMIN_ROLE_NAMES = frozenset({OWNER_ROLE_NAME, ADMIN_ROLE_NAME})

MembershipWithRole: TypeAlias = tuple[Membership, Role | None]


def normalized_role_name(role: Role | None) -> str | None:
    if role is None or role.deleted_at is not None:
        return None
    return role.name.lower()


def is_active_membership(membership: Membership) -> bool:
    return membership.deleted_at is None and membership.status == MembershipStatus.active


def has_role(role: Role | None, allowed_role_names: Iterable[str]) -> bool:
    role_name = normalized_role_name(role)
    if role_name is None:
        return False
    return role_name in allowed_role_names


def has_admin_role(role: Role | None) -> bool:
    return has_role(role, ADMIN_ROLE_NAMES)


def has_owner_role(role: Role | None) -> bool:
    return has_role(role, {OWNER_ROLE_NAME})
