from loguru import logger

from src.core.handler_base import HandlerBase
from src.core.unit_of_work import UnitOfWork
from src.domains.pauses.commands.remove_pause.command import RemovePauseCommand
from src.domains.shifts.command_repository import CommandShiftRepository


class RemovePauseCommandHandler(HandlerBase):
    def __init__(self, shift_repository: CommandShiftRepository) -> None:
        self._shift_repository = shift_repository

    async def handle(self, command: RemovePauseCommand) -> None:
        async with UnitOfWork() as session:
            shift = await self._shift_repository.get_by_pause_id(session, command.id)
            if shift is None:
                logger.debug(
                    "Remove pause command skipped; pause not found pause_id={}",
                    command.id,
                )
                return

            shift.delete_pause(command.id)
            await self._shift_repository.save(session, shift)
            await self.save_events(session, shift.pull_events())

        logger.info(
            "Remove pause command completed pause_id={} shift_id={}",
            command.id,
            shift.id,
        )
