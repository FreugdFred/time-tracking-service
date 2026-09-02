from datetime import UTC, datetime
from uuid import uuid4

from dependency_container import Dependency
from src.domains.pauses.entity import PauseEntity
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.clock_shift.command import ClockShiftCommand
from src.domains.shifts.commands.clock_shift.handler import ClockShiftCommandHandler
from src.domains.shifts.entity import ShiftEntity
from time_provider import FakeTimeProvider


NOW = datetime(2026, 9, 2, 10, tzinfo=UTC)


async def test_starts_shift_when_none_is_active(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)
    handler = Dependency.get(ClockShiftCommandHandler)

    shift_id = await handler.handle(ClockShiftCommand(reference_id="employee-1"))

    saved_shift = await command_shift_repository.get(shift_id)
    assert saved_shift is not None
    assert saved_shift.id == shift_id
    assert saved_shift.reference_id == "employee-1"
    assert saved_shift.started_at == NOW
    assert saved_shift.finished_at is None


async def test_finishes_active_shift_and_pause(
    time_provider: FakeTimeProvider,
    command_shift_repository: CommandShiftRepository,
) -> None:
    time_provider.travel(NOW)
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        pauses=[
            PauseEntity(
                shift_id=uuid4(),
                started_at=datetime(2026, 9, 2, 9, tzinfo=UTC),
            )
        ],
    )
    shift.pauses[0].shift_id = shift.id
    await command_shift_repository.save(shift)

    shift_id = await Dependency.get(ClockShiftCommandHandler).handle(
        ClockShiftCommand(reference_id=shift.reference_id)
    )

    saved_shift = await command_shift_repository.get(shift_id)
    assert saved_shift is not None
    assert saved_shift.finished_at == NOW
    assert saved_shift.pauses[0].finished_at == NOW
