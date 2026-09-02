from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dependency_container import Dependency
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.save_shift.command import SaveShiftCommand
from src.domains.shifts.commands.save_shift.handler import SaveShiftCommandHandler
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import OverlappingException, ValidationException
from time_provider import FakeTimeProvider


async def test_create_requires_complete_shift(
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift_id = uuid4()

    with pytest.raises(ValidationException):
        await Dependency.get(SaveShiftCommandHandler).handle(
            SaveShiftCommand(id=shift_id, reference_id="employee-1")
        )

    assert await command_shift_repository.get(shift_id) is None


async def test_create_persists_complete_shift(
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift_id = uuid4()

    result = await Dependency.get(SaveShiftCommandHandler).handle(
        SaveShiftCommand(
            id=shift_id,
            reference_id="employee-1",
            started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
            finished_at=datetime(2026, 9, 2, 17, tzinfo=UTC),
            approved=True,
        )
    )

    saved_shift = await command_shift_repository.get(shift_id)
    assert saved_shift is not None
    assert result == shift_id
    assert saved_shift.id == shift_id
    assert saved_shift.approved


async def test_update_applies_complete_time_range_atomically(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 10, tzinfo=UTC),
    )
    await command_shift_repository.save(shift)

    await Dependency.get(SaveShiftCommandHandler).handle(
        SaveShiftCommand(
            id=shift.id,
            started_at=datetime(2026, 9, 2, 11, tzinfo=UTC),
            finished_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
            approved=True,
            automatically_closed=True,
        )
    )

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.started_at == datetime(2026, 9, 2, 11, tzinfo=UTC)
    assert saved_shift.finished_at == datetime(2026, 9, 2, 12, tzinfo=UTC)
    assert saved_shift.approved
    assert saved_shift.automatically_closed


async def test_overlapping_shift_is_not_saved(
    command_shift_repository: CommandShiftRepository,
) -> None:
    existing_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    await command_shift_repository.save(existing_shift)
    new_shift_id = uuid4()

    with pytest.raises(OverlappingException):
        await Dependency.get(SaveShiftCommandHandler).handle(
            SaveShiftCommand(
                id=new_shift_id,
                reference_id="employee-1",
                started_at=datetime(2026, 9, 1, 9, tzinfo=UTC),
                finished_at=datetime(2026, 9, 1, 11, tzinfo=UTC),
            )
        )

    assert await command_shift_repository.get(new_shift_id) is None


async def test_updated_values_are_checked_for_overlap_before_save(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift = ShiftEntity(
        id=uuid4(),
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 10, tzinfo=UTC),
    )
    adjacent_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 6, tzinfo=UTC),
        finished_at=datetime(2026, 9, 1, 7, tzinfo=UTC),
    )
    await command_shift_repository.save(adjacent_shift)
    await command_shift_repository.save(shift)

    with pytest.raises(OverlappingException):
        await Dependency.get(SaveShiftCommandHandler).handle(
            SaveShiftCommand(
                id=shift.id,
                started_at=datetime(2026, 9, 1, 6, 30, tzinfo=UTC),
            )
        )

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.started_at == datetime(2026, 9, 1, 8, tzinfo=UTC)
