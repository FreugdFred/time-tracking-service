from uuid import UUID

from loguru import logger

from src.core.handler_base import HandlerBase
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.clock_shift.command import ClockShiftCommand
from src.domains.shifts.entity import ShiftEntity


class ClockShiftCommandHandler(HandlerBase):
    def __init__(self, shift_repository: CommandShiftRepository) -> None:
        self._shift_repository = shift_repository

    async def handle(self, command: ClockShiftCommand) -> UUID:
        active_shift = await self._shift_repository.get_active(
            reference_id=command.reference_id,
        )

        if active_shift is not None:
            active_shift.finish()
            action = "finished"
        else:
            active_shift = ShiftEntity.start(reference_id=command.reference_id)
            action = "started"

        await self._shift_repository.save(active_shift)
        logger.info(
            "Shift clock command completed action={} shift_id={}",
            action,
            active_shift.id,
        )

        await self.publish_events(active_shift.pull_events())
        return active_shift.id
