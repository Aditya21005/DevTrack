from __future__ import annotations

import logging
from types import TracebackType

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from devtrack_ai_db.database import DatabaseError
from devtrack_ai_db.session import DatabaseIntegrityError, DatabaseOperationalError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DatabaseIntegrityError, _handle_database_integrity_error)
    app.add_exception_handler(DatabaseOperationalError, _handle_database_operational_error)
    app.add_exception_handler(DatabaseError, _handle_database_error)


def _exc_info(exc: Exception) -> tuple[type[Exception], Exception, TracebackType | None]:
    return type(exc), exc, exc.__traceback__


async def _handle_database_integrity_error(_request: Request, exc: DatabaseIntegrityError) -> JSONResponse:
    logger.warning("api.database_integrity_error", exc_info=_exc_info(exc))
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database constraint violation"},
    )


async def _handle_database_operational_error(_request: Request, exc: DatabaseOperationalError) -> JSONResponse:
    logger.error("api.database_operational_error", exc_info=_exc_info(exc))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database operation failed"},
    )


async def _handle_database_error(_request: Request, exc: DatabaseError) -> JSONResponse:
    logger.error("api.database_error", exc_info=_exc_info(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error"},
    )
