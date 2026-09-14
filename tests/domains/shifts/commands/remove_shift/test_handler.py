from datetime import UTC, datetime
from uuid import uuid4

from dependency_container import Dependency
from src.core.unit_of_work import UnitOfWork
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.remove_shift.command import RemoveShiftCommand
from src.domains.shifts.commands.remove_shift.handler import RemoveShiftCommandHandler
from src.domains.shifts.entity import ShiftEntity


async def test_remove_delegates_idempotently_to_repository(
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift_id = uuid4()
    async with UnitOfWork() as session:
        await command_shift_repository.save(
            session,
            ShiftEntity(
                id=shift_id,
                reference_id="employee-1",
                started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
                finished_at=datetime(2026, 9, 2, 17, tzinfo=UTC),
            ),
        )

    await Dependency.get(RemoveShiftCommandHandler).handle(
        RemoveShiftCommand(id=shift_id)
    )

    await Dependency.get(RemoveShiftCommandHandler).handle(
        RemoveShiftCommand(id=shift_id)
    )

    async with UnitOfWork() as session:
        saved_shift = await command_shift_repository.get(session, shift_id)

    assert saved_shift is None
