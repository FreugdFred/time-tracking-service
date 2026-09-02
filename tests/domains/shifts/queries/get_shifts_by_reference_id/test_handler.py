from datetime import UTC, datetime

from dependency_container import Dependency
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.domains.shifts.queries.get_shifts_by_reference_id.handler import (
    GetShiftsByReferenceIdQueryHandler,
)
from src.domains.shifts.queries.get_shifts_by_reference_id.query import (
    GetShiftsByReferenceIdQuery,
)
from src.domains.shifts.query_models import ShiftByReferenceIdQueryModel
from src.domains.shifts.query_repository import QueryShiftRepository


async def test_applies_filters_sorting_and_pagination(
    command_shift_repository: CommandShiftRepository,
    query_shift_repository: QueryShiftRepository,
) -> None:
    matching_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
        automatically_closed=True,
        approved=False,
    )
    excluded_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 11, tzinfo=UTC),
        automatically_closed=True,
        approved=True,
    )
    await command_shift_repository.save(matching_shift)
    await command_shift_repository.save(excluded_shift)
    query = GetShiftsByReferenceIdQuery(
        reference_id="employee-1",
        approved=False,
        automatically_closed=True,
        is_open=False,
        sort_direction="asc",
        limit=10,
        offset=0,
    )

    result = await Dependency.get(GetShiftsByReferenceIdQueryHandler).handle(query)

    assert result.items == [
        ShiftByReferenceIdQueryModel.model_validate(matching_shift)
    ]
    assert result.total == 1
    assert result.limit == 10
    assert result.offset == 0
    assert await query_shift_repository.get_by_reference_id(
        "employee-1",
        approved=False,
        automatically_closed=True,
        is_open=False,
        sort_direction="asc",
        limit=10,
        offset=0,
    ) == result
