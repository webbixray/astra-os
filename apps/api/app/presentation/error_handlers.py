"""RFC 7807 Problem Details error handlers."""

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

logger = logging.getLogger(__name__)

# Problem type URIs
PROBLEM_TYPES = {
    400: "https://api.astra-os.com/problems/bad-request",
    401: "https://api.astra-os.com/problems/unauthorized",
    403: "https://api.astra-os.com/problems/forbidden",
    404: "https://api.astra-os.com/problems/not-found",
    422: "https://api.astra-os.com/problems/validation-error",
    429: "https://api.astra-os.com/problems/rate-limited",
    500: "https://api.astra-os.com/problems/internal-error",
    503: "https://api.astra-os.com/problems/service-unavailable",
}

PROBLEM_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Validation Error",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


def _problem_response(
    request: Request,
    status_code: int,
    detail: str,
    instance: str | None = None,
    **extensions,
) -> JSONResponse:
    """Create RFC 7807 Problem Details response."""
    problem_type = PROBLEM_TYPES.get(status_code, PROBLEM_TYPES[500])
    title = PROBLEM_TITLES.get(status_code, PROBLEM_TITLES[500])

    if instance is None:
        instance = str(request.url)

    content = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
    }

    # Add any extension fields
    content.update(extensions)

    return JSONResponse(status_code=status_code, content=content)


def register_error_handlers(app):
    """Register RFC 7807 compliant error handlers."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return _problem_response(request, 404, str(exc), code=exc.code)

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return _problem_response(request, 422, str(exc), code=exc.code)

    @app.exception_handler(UnauthorizedError)
    async def unauthorized(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return _problem_response(request, 401, str(exc), code=exc.code)

    @app.exception_handler(ForbiddenError)
    async def forbidden(request: Request, exc: ForbiddenError) -> JSONResponse:
        return _problem_response(request, 403, str(exc), code=exc.code)

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return _problem_response(request, 400, str(exc), code=exc.code)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem_response(request, exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_error_pydantic(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(loc_part) for loc_part in err.get("loc", []))
            errors.append({"field": loc, "message": err.get("msg", "")})
        return _problem_response(
            request,
            422,
            "Request validation failed",
            code="validation_error",
            errors=errors,
        )

    @app.exception_handler(Exception)
    async def generic_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return _problem_response(
            request,
            500,
            "An unexpected error occurred",
            code="internal_error",
        )

    return app
