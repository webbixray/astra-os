class DomainError(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: str = "domain_error") -> None:
        self.code = code
        super().__init__(message)


class EntityNotFoundError(DomainError):
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            message=f"{entity_type} not found: {entity_id}",
            code=f"{entity_type.lower()}_not_found",
        )


class ValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="validation_error")


class UnauthorizedError(DomainError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, code="unauthorized")


class ForbiddenError(DomainError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message=message, code="forbidden")
