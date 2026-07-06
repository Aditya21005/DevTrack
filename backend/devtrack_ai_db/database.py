from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

_ENGINE: AsyncEngine | None = None


class DatabaseError(RuntimeError):
    """Base exception for database infrastructure failures."""


class DatabaseConnectionError(DatabaseError):
    """Raised when the application cannot establish a database connection."""


class DatabaseHealthCheckError(DatabaseError):
    """Raised when a database health check fails."""


def create_database_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create a production-ready async SQLAlchemy engine.

    The engine is intentionally created in one place so API processes, workers,
    and Alembic configuration can share the same pooling and connection policy.
    """
    settings = settings or get_settings()

    try:
        engine = create_async_engine(
            settings.sqlalchemy_database_url,
            echo=settings.database_echo or settings.log_sql,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout_seconds,
            pool_recycle=settings.database_pool_recycle_seconds,
            pool_use_lifo=settings.database_pool_use_lifo,
            pool_pre_ping=True,
            future=True,
            connect_args={
                "application_name": settings.database_application_name,
            },
        )
    except SQLAlchemyError as exc:
        logger.exception("database.engine_create_failed")
        raise DatabaseConnectionError("Failed to create database engine") from exc

    _install_engine_event_handlers(engine, settings)
    logger.info(
        "database.engine_created",
        extra={
            "database_pool_size": settings.database_pool_size,
            "database_max_overflow": settings.database_max_overflow,
            "database_pool_timeout_seconds": settings.database_pool_timeout_seconds,
            "database_pool_recycle_seconds": settings.database_pool_recycle_seconds,
            "database_pool_use_lifo": settings.database_pool_use_lifo,
        },
    )
    return engine


def _install_engine_event_handlers(engine: AsyncEngine, settings: Settings) -> None:
    """Attach low-level connection hooks to enforce PostgreSQL session defaults."""

    @event.listens_for(engine.sync_engine, "connect")
    def configure_connection(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        with dbapi_connection.cursor() as cursor:
            cursor.execute(
                "SET application_name = %s",
                (settings.database_application_name,),
            )
            cursor.execute(
                "SET statement_timeout = %s",
                (settings.database_statement_timeout_ms,),
            )
            cursor.execute(
                "SET lock_timeout = %s",
                (settings.database_lock_timeout_ms,),
            )

    @event.listens_for(engine.sync_engine, "checkout")
    def log_connection_checkout(_dbapi_connection, _connection_record, _connection_proxy) -> None:  # type: ignore[no-untyped-def]
        logger.debug("database.connection_checked_out")

    @event.listens_for(engine.sync_engine, "checkin")
    def log_connection_checkin(_dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        logger.debug("database.connection_checked_in")


def get_engine() -> AsyncEngine:
    """Return the process-wide database engine, creating it lazily."""
    global _ENGINE

    if _ENGINE is None:
        _ENGINE = create_database_engine()
    return _ENGINE


async def initialize_database() -> None:
    """Initialize and verify database connectivity during application startup."""
    engine = get_engine()
    await check_database_health(engine)
    logger.info("database.initialized")


async def close_database() -> None:
    """Dispose database connections during graceful shutdown."""
    global _ENGINE

    if _ENGINE is not None:
        await _ENGINE.dispose()
        _ENGINE = None
        logger.info("database.disposed")


async def check_database_health(engine: AsyncEngine | None = None) -> None:
    """Run a minimal health check against PostgreSQL."""
    engine = engine or get_engine()

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("database.health_check_failed")
        raise DatabaseHealthCheckError("Database health check failed") from exc


@asynccontextmanager
async def database_connection() -> AsyncIterator[AsyncConnection]:
    """Provide a raw async connection for infrastructure tasks.

    Normal request handling should use the session dependency from session.py.
    This helper is reserved for health checks, migrations, maintenance jobs, and
    one-off infrastructure operations.
    """
    engine = get_engine()

    try:
        async with engine.connect() as connection:
            yield connection
    except SQLAlchemyError as exc:
        logger.exception("database.connection_error")
        raise DatabaseConnectionError("Database connection failed") from exc
