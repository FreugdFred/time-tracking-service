from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse

from src.exceptions import (
    AlreadyActiveException,
    AlreadyFinishedException,
    InvalidTimeRangeException,
    NotFoundException,
    OverlappingException,
    UnfinishedException,
    ValidationException,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundException)
    async def handle_not_found(_request: Request, exception: NotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exception)},
        )

    @app.exception_handler(ValidationException)
    async def handle_validation_error(_request: Request, exception: ValidationException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exception)},
        )

    @app.exception_handler(InvalidTimeRangeException)
    async def handle_invalid_time_range(
        _request: Request,
        exception: InvalidTimeRangeException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": str(exception)},
        )

    @app.exception_handler(AlreadyActiveException)
    @app.exception_handler(AlreadyFinishedException)
    @app.exception_handler(UnfinishedException)
    async def handle_state_conflict(
        _request: Request,
        exception: (
            AlreadyActiveException | AlreadyFinishedException | UnfinishedException
        ),
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exception)},
        )

    @app.exception_handler(OverlappingException)
    async def handle_overlapping(
        _request: Request,
        exception: OverlappingException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exception)},
        )
