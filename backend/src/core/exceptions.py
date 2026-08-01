class AppError(Exception):
    """Base class for domain errors translated into HTTP responses by main.py."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class ValidationError(AppError):
    """Maps to HTTP 400. Raised for bad input the caller can fix (FR-012, FR-016, FR-034)."""


class AuthenticationError(AppError):
    """Maps to HTTP 401. Raised for missing/invalid/expired credentials or tokens."""


class PermissionDeniedError(AppError):
    """Maps to HTTP 403. Raised when a role isn't allowed to perform an action (FR-003)."""


class NotFoundError(AppError):
    """Maps to HTTP 404. Raised when a referenced entity doesn't exist."""


class ConflictError(AppError):
    """Maps to HTTP 409. Raised for state conflicts (e.g. duplicate/expired resource)."""


class AIServiceUnavailableError(AppError):
    """Maps to HTTP 503. Raised when the configured AI provider can't be
    reached/initialized (FR-033) — every non-AI endpoint is unaffected."""
