import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions.domain_exceptions import (
    DomainError,
    EntityNotFoundError,
    ForbiddenError,
    UnauthorizedError,
    ValidationError,
)
from app.presentation.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message, details=details).model_dump(exclude_none=True),
    )


def register_error_handlers(app):
    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return _error_response(404, exc.code, str(exc))

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(422, exc.code, str(exc))

    @app.exception_handler(UnauthorizedError)
    async def unauthorized(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return _error_response(401, exc.code, str(exc))

    @app.exception_handler(ForbiddenError)
    async def forbidden(request: Request, exc: ForbiddenError) -> JSONResponse:
        return _error_response(403, exc.code, str(exc))

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return _error_response(400, exc.code, str(exc))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "http_error", exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_error_pydantic(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(loc_part) for loc_part in err.get("loc", []))
            errors.append({"field": loc, "message": err.get("msg", "")})
        return JSONResponse(
            status_code=422,
            content={"success": False, "code": "validation_error", "message": "Request validation failed", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def generic_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return _error_response(
            500,
            "internal_error",
            "An unexpected error occurred",
        )

    return app
