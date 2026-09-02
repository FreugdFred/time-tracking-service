from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from dependency_container import Dependency
from src.domains.shifts.commands.clock_shift.command import ClockShiftCommand
from src.domains.shifts.commands.clock_shift.handler import ClockShiftCommandHandler
from src.domains.shifts.commands.remove_shift.command import RemoveShiftCommand
from src.domains.shifts.commands.remove_shift.handler import RemoveShiftCommandHandler
from src.domains.shifts.commands.save_shift.command import SaveShiftCommand
from src.domains.shifts.commands.save_shift.handler import SaveShiftCommandHandler
from src.domains.shifts.queries.get_shift_by_id.handler import GetShiftByIdQueryHandler
from src.domains.shifts.queries.get_shift_by_id.query import GetShiftByIdQuery
from src.domains.shifts.queries.get_shifts_by_reference_id.handler import (
    GetShiftsByReferenceIdQueryHandler,
)
from src.domains.shifts.queries.get_shifts_by_reference_id.query import (
    GetShiftsByReferenceIdQuery,
)
from src.domains.shifts.queries.get_shifts_in_date_range.handler import (
    GetShiftsInDateRangeQueryHandler,
)
from src.domains.shifts.queries.get_shifts_in_date_range.query import (
    GetShiftsInDateRangeQuery,
)
from src.domains.shifts.query_models import (
    PaginatedQueryModel,
    ShiftByReferenceIdQueryModel,
    ShiftQueryModel,
)
from src.domains.shifts.schemas import (
    DateRangeInput,
    PaginationInput,
    SaveShiftInput,
    ShiftFiltersInput,
)

shift_router = APIRouter(prefix="/shift", tags=["shift"])


@shift_router.post("/clock")
async def clock_shift(reference_id: str) -> UUID:
    handler = Dependency.get(ClockShiftCommandHandler)
    return await handler.handle(ClockShiftCommand(reference_id=reference_id))


@shift_router.post("/save")
async def save_shift(input: SaveShiftInput) -> None:
    handler = Dependency.get(SaveShiftCommandHandler)
    await handler.handle(
        SaveShiftCommand(
            id=input.id,
            reference_id=input.reference_id,
            started_at=input.started_at,
            finished_at=input.finished_at,
            automatically_closed=input.automatically_closed,
            approved=input.approved,
        )
    )


@shift_router.delete("/remove")
async def remove_shift(id: UUID) -> None:
    handler = Dependency.get(RemoveShiftCommandHandler)
    await handler.handle(RemoveShiftCommand(id=id))



@shift_router.get(
    "/reference/{reference_id}",
    response_model=PaginatedQueryModel[ShiftByReferenceIdQueryModel],
)
async def get_shifts_by_reference_id(
    reference_id: str,
    filters: Annotated[ShiftFiltersInput, Depends()],
    pagination: Annotated[PaginationInput, Depends()],
) -> PaginatedQueryModel[ShiftByReferenceIdQueryModel]:
    handler = Dependency.get(GetShiftsByReferenceIdQueryHandler)
    return await handler.handle(
        GetShiftsByReferenceIdQuery(
            reference_id=reference_id,
            approved=filters.approved,
            automatically_closed=filters.automatically_closed,
            is_open=filters.is_open,
            sort_direction=filters.sort_direction,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    )


@shift_router.get(
    "/date-range",
    response_model=PaginatedQueryModel[ShiftQueryModel],
)
async def get_shifts_by_date_range(
    date_range: Annotated[DateRangeInput, Depends()],
    filters: Annotated[ShiftFiltersInput, Depends()],
    pagination: Annotated[PaginationInput, Depends()],
    reference_id: str | None = None,
) -> PaginatedQueryModel[ShiftQueryModel]:
    handler = Dependency.get(GetShiftsInDateRangeQueryHandler)
    return await handler.handle(
        GetShiftsInDateRangeQuery(
            reference_id=reference_id,
            start=date_range.start,
            end=date_range.end,
            approved=filters.approved,
            automatically_closed=filters.automatically_closed,
            is_open=filters.is_open,
            sort_direction=filters.sort_direction,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    )


@shift_router.get("/{id}", response_model=ShiftQueryModel)
async def get_shift(id: UUID) -> ShiftQueryModel:
    handler = Dependency.get(GetShiftByIdQueryHandler)
    return await handler.handle(GetShiftByIdQuery(id=id))
