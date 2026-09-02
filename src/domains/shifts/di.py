from dependency_container import Dependency
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.close_open_shifts.handler import (
    CloseOpenShiftsCommandHandler,
)
from src.domains.shifts.commands.clock_shift.handler import ClockShiftCommandHandler
from src.domains.shifts.commands.remove_shift.handler import RemoveShiftCommandHandler
from src.domains.shifts.commands.save_shift.handler import SaveShiftCommandHandler
from src.domains.shifts.queries.get_shift_by_id.handler import GetShiftByIdQueryHandler
from src.domains.shifts.queries.get_shifts_by_reference_id.handler import (
    GetShiftsByReferenceIdQueryHandler,
)
from src.domains.shifts.queries.get_shifts_in_date_range.handler import (
    GetShiftsInDateRangeQueryHandler,
)
from src.domains.shifts.query_repository import QueryShiftRepository


def include_shift_dependencies() -> None:
    Dependency.register(CommandShiftRepository, CommandShiftRepository)
    Dependency.register(QueryShiftRepository, QueryShiftRepository)

    Dependency.register(ClockShiftCommandHandler, ClockShiftCommandHandler)
    Dependency.register(CloseOpenShiftsCommandHandler, CloseOpenShiftsCommandHandler)
    Dependency.register(RemoveShiftCommandHandler, RemoveShiftCommandHandler)
    Dependency.register(SaveShiftCommandHandler, SaveShiftCommandHandler)

    Dependency.register(GetShiftByIdQueryHandler, GetShiftByIdQueryHandler)
    Dependency.register(GetShiftsByReferenceIdQueryHandler, GetShiftsByReferenceIdQueryHandler)
    Dependency.register(GetShiftsInDateRangeQueryHandler, GetShiftsInDateRangeQueryHandler)
