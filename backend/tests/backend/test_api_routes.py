from __future__ import annotations

import pytest

from devtrack_ai_auth.routes import router as auth_router
from devtrack_ai_projects.routes import router as projects_router


pytestmark = pytest.mark.api


def route_paths(router) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in router.routes:
        methods = getattr(route, "methods", set()) or set()
        for method in methods:
            routes.add((method, route.path))
    return routes


def test_auth_router_exposes_required_authentication_contract() -> None:
    paths = route_paths(auth_router)

    assert ("POST", "/auth/register") in paths
    assert ("POST", "/auth/login") in paths
    assert ("POST", "/auth/refresh") in paths
    assert ("POST", "/auth/logout") in paths
    assert ("GET", "/auth/me") in paths
    assert ("GET", "/auth/protected") in paths


def test_project_router_exposes_crud_and_status_contracts() -> None:
    paths = route_paths(projects_router)

    assert ("POST", "/workspaces/{workspace_id}/projects") in paths
    assert ("GET", "/workspaces/{workspace_id}/projects") in paths
    assert ("GET", "/workspaces/{workspace_id}/projects/{project_id}") in paths
    assert ("PATCH", "/workspaces/{workspace_id}/projects/{project_id}") in paths
    assert ("DELETE", "/workspaces/{workspace_id}/projects/{project_id}") in paths
    assert ("PATCH", "/workspaces/{workspace_id}/projects/{project_id}/status") in paths