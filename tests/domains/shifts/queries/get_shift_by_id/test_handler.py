from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dependency_container import Dependency
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.domains.shifts.queries.get_shift_by_id.handler import (
    GetShiftByIdQueryHandler,
)
from src.domains.shifts.queries.get_shift_by_id.query import GetShiftByIdQuery
from src.domains.shifts.query_models import ShiftQueryModel
from src.domains.shifts.query_repository import QueryShiftRepository
from src.exceptions import NotFoundException


async def test_returns_shift_projection(
    command_shift_repository: CommandShiftRepository,
    query_shift_repository: QueryShiftRepository,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 17, tzinfo=UTC),
        pauses=[],
        automatically_closed=False,
        approved=True,
    )
    await command_shift_repository.save(shift)

    result = await Dependency.get(GetShiftByIdQueryHandler).handle(
        GetShiftByIdQuery(id=shift.id)
    )

    assert result == ShiftQueryModel.model_validate(shift)
    assert await query_shift_repository.get(shift.id) == result


async def test_raises_for_missing_shift(
    query_shift_repository: QueryShiftRepository,
) -> None:
    shift_id = uuid4()

    with pytest.raises(NotFoundException):
        await Dependency.get(GetShiftByIdQueryHandler).handle(
            GetShiftByIdQuery(id=shift_id)
        )

    assert await query_shift_repository.get(shift_id) is None
