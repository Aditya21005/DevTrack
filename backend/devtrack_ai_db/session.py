from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import DatabaseError, get_engine

logger = logging.getLogger(__name__)

_SESSION_FACTORY: async_sessionmaker[AsyncSession] | None = None


class DatabaseSessionError(DatabaseError):
    """Raised when session lifecycle management fails."""


class DatabaseIntegrityError(DatabaseSessionError):
    """Raised when a database constraint is violated."""


class DatabaseOperationalError(DatabaseSessionError):
    """Raised when PostgreSQL or the network cannot complete an operation."""


def create_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create the process-wide async session factory.

    expire_on_commit=False keeps ORM attributes available after commits, which
    avoids accidental lazy-loading after the request session has closed.
    autoflush=False makes writes explicit and prevents surprise flushes from
    read queries inside service-layer validation.
    """
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the lazily initialized async session factory."""
    global _SESSION_FACTORY

    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = create_session_factory()
        logger.info("database.session_factory_created")
    return _SESSION_FACTORY


def reset_session_factory() -> None:
    """Reset the cached session factory.

    This is mainly useful for tests that replace the engine or for application
    shutdown paths that want a clean process state.
    """
    global _SESSION_FACTORY
    _SESSION_FACTORY = None
    logger.info("database.session_factory_reset")


def translate_sqlalchemy_error(exc: SQLAlchemyError) -> DatabaseSessionError:
    """Map SQLAlchemy exceptions to stable infrastructure exceptions."""
    if isinstance(exc, IntegrityError):
        return DatabaseIntegrityError("Database constraint violation")
    if isinstance(exc, OperationalError):
        return DatabaseOperationalError("Database operation failed")
    return DatabaseSessionError("Database session operation failed")


async def rollback_safely(session: AsyncSession) -> None:
    """Rollback without masking the original exception."""
    try:
        if session.in_transaction():
            await session.rollback()
    except SQLAlchemyError:
        logger.exception("database.session_rollback_failed")


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a service/worker-friendly transactional session scope.

    The transaction commits when the block exits successfully and rolls back for
    any exception. FastAPI request dependencies below use the same behavior for
    HTTP handlers.
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await rollback_safely(session)
            translated = translate_sqlalchemy_error(exc)
            logger.exception(
                "database.session_error",
                extra={"database_error_type": translated.__class__.__name__},
            )
            raise translated from exc
        except Exception:
            await rollback_safely(session)
            raise


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that provides a plain async session.

    Use this dependency when services own transaction boundaries explicitly. It
    never commits automatically, but it does rollback open transactions on error
    and always closes the session at the end of the request.
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
        except SQLAlchemyError as exc:
            await rollback_safely(session)
            translated = translate_sqlalchemy_error(exc)
            logger.exception(
                "database.session_dependency_error",
                extra={"database_error_type": translated.__class__.__name__},
            )
            raise translated from exc
        except Exception:
            await rollback_safely(session)
            raise
        finally:
            await session.close()


async def get_transactional_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that commits on success and rolls back on failure.

    This is useful for command endpoints whose route handler represents a single
    unit of work. Prefer explicit service-level transactions for complex flows
    that call external systems or need multiple transaction boundaries.
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as exc:
            await rollback_safely(session)
            translated = translate_sqlalchemy_error(exc)
            logger.exception(
                "database.transactional_session_error",
                extra={"database_error_type": translated.__class__.__name__},
            )
            raise translated from exc
        except Exception:
            await rollback_safely(session)
            raise
        finally:
            await session.close()
