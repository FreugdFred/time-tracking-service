from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dependency_container import Dependency
from src.domains.pauses.entity import PauseEntity
from src.domains.pauses.queries.get_pause_by_id.handler import (
    GetPauseByIdQueryHandler,
)
from src.domains.pauses.queries.get_pause_by_id.query import GetPauseByIdQuery
from src.domains.pauses.query_models import PauseQueryModel
from src.domains.pauses.query_repository import QueryPauseRepository
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import NotFoundException


async def test_returns_pause_with_shift_id(
    command_shift_repository: CommandShiftRepository,
    query_pause_repository: QueryPauseRepository,
) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    shift = ShiftEntity(
        id=pause.shift_id,
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 17, tzinfo=UTC),
        pauses=[pause],
    )
    await command_shift_repository.save(shift)

    result = await Dependency.get(GetPauseByIdQueryHandler).handle(
        GetPauseByIdQuery(id=pause.id)
    )

    assert result == PauseQueryModel(
        id=pause.id,
        shift_id=shift.id,
        started_at=pause.started_at,
        finished_at=pause.finished_at,
    )
    assert await query_pause_repository.get(pause.id) == result


async def test_raises_when_pause_does_not_exist(
    query_pause_repository: QueryPauseRepository,
) -> None:
    pause_id = uuid4()

    with pytest.raises(NotFoundException):
        await Dependency.get(GetPauseByIdQueryHandler).handle(
            GetPauseByIdQuery(id=pause_id)
        )

    assert await query_pause_repository.get(pause_id) is None
