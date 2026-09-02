from datetime import UTC, datetime

from dependency_container import Dependency
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.domains.shifts.queries.get_shifts_in_date_range.handler import (
    GetShiftsInDateRangeQueryHandler,
)
from src.domains.shifts.queries.get_shifts_in_date_range.query import (
    GetShiftsInDateRangeQuery,
)
from src.domains.shifts.query_models import ShiftQueryModel
from src.domains.shifts.query_repository import QueryShiftRepository


async def test_applies_filters_sorting_and_pagination(
    command_shift_repository: CommandShiftRepository,
    query_shift_repository: QueryShiftRepository,
) -> None:
    matching_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        automatically_closed=False,
        approved=True,
    )
    excluded_shift = ShiftEntity(
        reference_id="employee-2",
        started_at=datetime(2026, 9, 2, 9, tzinfo=UTC),
    )
    await command_shift_repository.save(matching_shift)
    await command_shift_repository.save(excluded_shift)
    start = datetime(2026, 9, 1, tzinfo=UTC)
    end = datetime(2026, 9, 3, tzinfo=UTC)
    query = GetShiftsInDateRangeQuery(
        reference_id="employee-1",
        start=start,
        end=end,
        approved=True,
        automatically_closed=False,
        is_open=True,
        sort_direction="desc",
        limit=25,
        offset=5,
    )

    result = await Dependency.get(GetShiftsInDateRangeQueryHandler).handle(query)

    assert result.items == []
    assert result.total == 1
    assert result.limit == 25
    assert result.offset == 5
    first_page = await query_shift_repository.get_by_date_range(
        start_date=start,
        end_date=end,
        reference_id="employee-1",
        approved=True,
        automatically_closed=False,
        is_open=True,
        sort_direction="desc",
        limit=25,
        offset=0,
    )
    assert first_page.items == [ShiftQueryModel.model_validate(matching_shift)]
