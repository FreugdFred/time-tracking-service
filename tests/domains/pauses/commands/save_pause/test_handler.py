from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dependency_container import Dependency
from src.domains.pauses.commands.save_pause.command import SavePauseCommand
from src.domains.pauses.commands.save_pause.handler import SavePauseCommandHandler
from src.domains.pauses.entity import PauseEntity
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import (
    NotFoundException,
    OverlappingException,
    UnfinishedException,
    ValidationException,
)
from time_provider import FakeTimeProvider


async def test_create_requires_complete_pause(
    command_shift_repository: CommandShiftRepository,
) -> None:
    pause_id = uuid4()
    with pytest.raises(ValidationException):
        await Dependency.get(SavePauseCommandHandler).handle(
            SavePauseCommand(id=pause_id, shift_id=uuid4())
        )

    assert await command_shift_repository.get_by_pause_id(pause_id) is None


async def test_create_for_unknown_shift_raises(
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift_id = uuid4()

    with pytest.raises(NotFoundException):
        await Dependency.get(SavePauseCommandHandler).handle(
            SavePauseCommand(
                id=uuid4(),
                shift_id=shift_id,
                started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
                finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
            )
        )

    assert await command_shift_repository.get(shift_id) is None


async def test_create_requires_finished_shift(
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
    )
    await command_shift_repository.save(shift)

    with pytest.raises(UnfinishedException):
        await Dependency.get(SavePauseCommandHandler).handle(
            SavePauseCommand(
                id=uuid4(),
                shift_id=shift.id,
                started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
                finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
            )
        )

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.pauses == []


async def test_create_adds_pause_to_finished_shift(
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift = ShiftEntity(
        id=uuid4(),
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 17, tzinfo=UTC),
    )
    await command_shift_repository.save(shift)
    pause_id = uuid4()

    result = await Dependency.get(SavePauseCommandHandler).handle(
        SavePauseCommand(
            id=pause_id,
            shift_id=shift.id,
            started_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
            finished_at=datetime(2026, 9, 1, 13, tzinfo=UTC),
        )
    )

    assert result == pause_id
    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.get_pause(pause_id).shift_id == shift.id


async def test_update_validates_and_applies_final_range_atomically(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    pause_id = uuid4()
    shift = ShiftEntity(
        id=uuid4(),
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 7, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
        pauses=[
            PauseEntity(
                id=pause_id,
                shift_id=uuid4(),
                started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
                finished_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
            ),
            PauseEntity(
                shift_id=uuid4(),
                started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
                finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
            ),
        ],
    )
    for pause in shift.pauses:
        pause.shift_id = shift.id
    await command_shift_repository.save(shift)

    await Dependency.get(SavePauseCommandHandler).handle(
        SavePauseCommand(
            id=pause_id,
            started_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
            finished_at=datetime(2026, 9, 1, 11, tzinfo=UTC),
        )
    )

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    pause = saved_shift.get_pause(pause_id)
    assert pause.started_at == datetime(2026, 9, 1, 10, tzinfo=UTC)
    assert pause.finished_at == datetime(2026, 9, 1, 11, tzinfo=UTC)


async def test_update_cannot_move_pause_to_another_shift(
    command_shift_repository: CommandShiftRepository,
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

    with pytest.raises(ValidationException):
        await Dependency.get(SavePauseCommandHandler).handle(
            SavePauseCommand(id=pause.id, shift_id=uuid4())
        )

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.get_pause(pause.id).shift_id == shift.id


async def test_update_rejects_overlapping_pause(
    command_shift_repository: CommandShiftRepository,
) -> None:
    first = PauseEntity(
        shift_id=uuid4(),
        started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    second = PauseEntity(
        shift_id=first.shift_id,
        started_at=datetime(2026, 9, 1, 11, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 12, tzinfo=UTC),
    )
    shift = ShiftEntity(
        id=first.shift_id,
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 17, tzinfo=UTC),
        pauses=[first, second],
    )
    await command_shift_repository.save(shift)

    with pytest.raises(OverlappingException):
        await Dependency.get(SavePauseCommandHandler).handle(
            SavePauseCommand(
                id=second.id,
                started_at=datetime(2026, 9, 1, 9, 30, tzinfo=UTC),
            )
        )

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    saved_second = saved_shift.get_pause(second.id)
    assert saved_second.started_at == datetime(2026, 9, 1, 11, tzinfo=UTC)
