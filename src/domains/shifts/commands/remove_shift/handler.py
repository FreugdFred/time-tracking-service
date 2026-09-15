from loguru import logger

from src.core.handler_base import HandlerBase
from src.core.unit_of_work import UnitOfWork
from domains.shifts.commands.repository import CommandShiftRepository
from src.domains.shifts.commands.remove_shift.command import RemoveShiftCommand


class RemoveShiftCommandHandler(HandlerBase):
    def __init__(self, shift_repository: CommandShiftRepository) -> None:
        self._shift_repository = shift_repository

    async def handle(self, command: RemoveShiftCommand) -> None:
        async with UnitOfWork() as session:
            shift = await self._shift_repository.get(session, command.id)
            if shift is None:
                logger.debug(
                    "Remove shift command skipped; shift not found shift_id={}",
                    command.id,
                )
                return

            shift.delete()
            await self._shift_repository.remove(session, shift.id)
            await self.save_events(session, shift.pull_events())

        logger.info("Remove shift command completed shift_id={}", command.id)
