from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from devtrack_ai_api.exception_handlers import register_exception_handlers
from devtrack_ai_api.rate_limit import RateLimitExceededError, rate_limit_exception_handler
from devtrack_ai_auth.routes import router as auth_router
from devtrack_ai_dashboard.routes import router as dashboard_router
from devtrack_ai_db.config import get_settings
from devtrack_ai_db.database import check_database_health, close_database, initialize_database
from devtrack_ai_kanban.routes import router as kanban_router
from devtrack_ai_projects.routes import router as projects_router
from devtrack_ai_tasks.routes import router as tasks_router
from devtrack_ai_workspace.routes import router as workspace_router

logger = logging.getLogger(__name__)


def _csv_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [value.strip() for value in raw_value.split(",") if value.strip()]


def _validate_production_network_policy(*, is_production: bool, allowed_hosts: list[str], allowed_origins: list[str]) -> None:
    if not is_production:
        return
    if "*" in allowed_hosts:
        raise ValueError("DEVTRACK_ALLOWED_HOSTS cannot contain '*' in production")
    if "*" in allowed_origins:
        raise ValueError("DEVTRACK_CORS_ALLOWED_ORIGINS cannot contain '*' in production")

    insecure_origins = []
    for origin in allowed_origins:
        parsed = urlparse(origin)
        if parsed.scheme != "https":
            insecure_origins.append(origin)
    if insecure_origins:
        raise ValueError("Production CORS origins must use HTTPS")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await initialize_database()
    try:
        yield
    finally:
        await close_database()


def create_app() -> FastAPI:
    settings = get_settings()
    allowed_hosts = _csv_env("DEVTRACK_ALLOWED_HOSTS", "localhost,127.0.0.1")
    allowed_origins = _csv_env("DEVTRACK_CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
    _validate_production_network_policy(
        is_production=settings.is_production,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )

    register_exception_handlers(app)
    app.add_exception_handler(RateLimitExceededError, rate_limit_exception_handler)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if settings.is_production and request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", settings.request_id_header],
    )

    app.include_router(auth_router, prefix="/api")
    app.include_router(workspace_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(kanban_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")

    @app.get("/health/live", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok", "service": "devtrack-ai-api"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> JSONResponse:
        try:
            await check_database_health()
        except Exception:
            logger.exception("health.readiness_failed")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unavailable", "dependency": "postgresql"},
            )
        return JSONResponse(content={"status": "ready", "dependency": "postgresql"})

    return app


app = create_app()
