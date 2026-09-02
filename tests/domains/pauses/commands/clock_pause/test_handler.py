from datetime import UTC, datetime
from uuid import uuid4

import pytest

from dependency_container import Dependency
from src.domains.pauses.commands.clock_pause.command import ClockPauseCommand
from src.domains.pauses.commands.clock_pause.handler import ClockPauseCommandHandler
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import NotFoundException
from time_provider import FakeTimeProvider


NOW = datetime(2026, 9, 1, 9, tzinfo=UTC)


async def test_starts_and_then_finishes_active_pause(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)
    shift = ShiftEntity(
        id=uuid4(),
        reference_id="employee-1",
        started_at=datetime(2026, 9, 1, 8, tzinfo=UTC),
    )
    await command_shift_repository.save(shift)
    handler = Dependency.get(ClockPauseCommandHandler)

    pause_id = await handler.handle(ClockPauseCommand(reference_id=shift.reference_id))

    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    active_pause = saved_shift.active_pause
    assert active_pause is not None
    assert active_pause.id == pause_id
    assert active_pause.started_at == NOW

    time_provider.travel(datetime(2026, 9, 1, 10, tzinfo=UTC))
    finished_pause_id = await handler.handle(
        ClockPauseCommand(reference_id=shift.reference_id)
    )

    assert finished_pause_id == pause_id
    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.active_pause is None
    assert saved_shift.get_pause(pause_id).finished_at == datetime(
        2026, 9, 1, 10, tzinfo=UTC
    )


async def test_requires_active_shift_for_reference(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)

    with pytest.raises(NotFoundException) as exception_info:
        await Dependency.get(ClockPauseCommandHandler).handle(
            ClockPauseCommand(reference_id="employee-1")
        )

    assert str(exception_info.value) == (
        "Cannot clock a pause because no active shift was found for reference "
        "'employee-1'. Start a shift first."
    )
    assert await command_shift_repository.get_active("employee-1") is None
