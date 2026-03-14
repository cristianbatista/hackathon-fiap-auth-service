import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging import get_logger

logger = get_logger(__name__)


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class TokenExpiredError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning(
        "HTTP exception",
        extra={
            "trace_id": getattr(request.state, "trace_id", ""),
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "trace_id": getattr(request.state, "trace_id", ""),
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
