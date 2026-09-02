from datetime import date, datetime

from fastapi import HTTPException, status


class HTTPBadRequestException(HTTPException):
    """Base exception for bad request errors (HTTP 400)."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class HTTPConflictException(HTTPException):
    """Base exception for resource conflict / already exists errors."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class HTTPForbiddenException(HTTPException):
    """Base exception for forbidden access errors."""

    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class HTTPNotFoundException(HTTPException):
    """Base exception for resource not found errors."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class HTTPUnauthorizedException(HTTPException):
    """Base exception for unauthorized access errors."""

    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(Exception):
    """Raised when an authenticated actor cannot operate on a domain object."""


class AlreadyActiveException(Exception):
    """Exception raised when an action would create a duplicate active object."""

    def __init__(self, model: type, identifier: str | None = None):
        """
        Args:
            model: The model class that already has an active instance.
            identifier: Optional identifier for the related object.
        """
        model_name = getattr(model, "__name__", str(model))
        if identifier:
            message = f"{model_name} with identifier '{identifier}' is already active."
        else:
            message = f"{model_name} is already active."
        super().__init__(message)


class AlreadyExistsException(Exception):
    """Exception raised when a requested model instance already exists."""

    def __init__(self, model: type, identifier: str | None = None):
        """
        Args:
            model: The model class that already exists.
            identifier: Optional identifier for the specific instance (e.g., ID).
        """
        model_name = model.__name__ if hasattr(model, "__name__") else str(model)
        if identifier:
            message = f"{model_name} with identifier '{identifier}' already exists."
        else:
            message = f"{model_name} already exists."
        super().__init__(message)


class AlreadyFinishedException(Exception):
    """Exception raised when an action is performed on an already finished object."""

    def __init__(self, model: type, identifier: str | None = None):
        """
        Args:
            model: The model class that is already finished.
            identifier: Optional identifier for the specific instance (e.g., ID).
        """
        model_name = getattr(model, "__name__", str(model))
        if identifier:
            message = (
                f"{model_name} with identifier '{identifier}' is already finished."
            )
        else:
            message = f"{model_name} is already finished."
        super().__init__(message)


class UnfinishedException(Exception):
    """Exception raised when an action requires a finished object."""

    def __init__(self, model: type, identifier: str | None = None):
        """
        Args:
            model: The model class that is not finished.
            identifier: Optional identifier for the specific instance (e.g., ID).
        """
        model_name = getattr(model, "__name__", str(model))
        if identifier:
            message = f"{model_name} with identifier '{identifier}' is not finished."
        else:
            message = f"{model_name} is not finished."
        super().__init__(message)


class InvalidTimeRangeException(Exception):
    """Exception raised when an object's time range is invalid."""

    def __init__(
        self,
        model: type,
        identifier: str | None = None,
        start: datetime | date | None = None,
        end: datetime | date | None = None,
        detail: str | None = None,
    ):
        """
        Args:
            model: The model class that has the invalid time range.
            identifier: Optional identifier for the object (e.g., user ID, resource ID).
            start: Optional start datetime.
            end: Optional end datetime.
            detail: Optional additional message explaining why the range is invalid.
        """
        model_name = getattr(model, "__name__", str(model))
        parts = [model_name]

        if identifier:
            parts.append(f"'{identifier}'")
        if start or end:
            parts.append(f"start: {start}, end: {end}")
        if detail:
            parts.append(f"- {detail}")

        message = " ".join(parts)
        super().__init__(message)


class NotFoundException(Exception):
    """Exception raised when a requested model instance is not found."""

    def __init__(
        self,
        model: type,
        identifier: str | None = None,
        *,
        detail: str | None = None,
    ):
        """
        Args:
            model: The model class that was not found.
            identifier: Optional identifier for the specific instance (e.g., ID).
            detail: Optional context-specific error message.
        """
        if detail is not None:
            super().__init__(detail)
            return

        model_name = model.__name__ if hasattr(model, "__name__") else str(model)
        if identifier:
            message = f"{model_name} with identifier '{identifier}' not found."
        else:
            message = f"{model_name} not found."
        super().__init__(message)


class ValidationException(Exception):
    """Raised when a domain command does not contain valid input."""


class OverlappingException(Exception):
    """Exception raised when a new object overlaps with an existing object."""

    def __init__(
        self,
        model: type,
        identifier: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ):
        """
        Args:
            model: The model class that has the overlapping instance.
            identifier: Optional identifier for the object (e.g., user ID, resource ID).
            start: Optional start of the new range.
            end: Optional end of the new range.
        """
        model_name = model.__name__ if hasattr(model, "__name__") else str(model)
        parts = [f"{model_name}"]

        if identifier:
            parts.append(f"'{identifier}'")
        if start:
            parts.append(f"from {start}")
        if end:
            parts.append(f"to {end}")

        message = " ".join(parts) + " overlaps with an existing object."
        super().__init__(message)
