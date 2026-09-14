from datetime import timedelta

from loguru import logger

from src.core.handler_base import HandlerBase
from src.core.unit_of_work import UnitOfWork
from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.commands.close_open_shifts.command import (
    CloseOpenShiftsCommand,
)
from time_provider import AbstractTimeProvider


class CloseOpenShiftsCommandHandler(HandlerBase):
    def __init__(
        self,
        shift_repository: CommandShiftRepository,
        time_provider: AbstractTimeProvider,
    ) -> None:
        self._shift_repository = shift_repository
        self._time_provider = time_provider

    async def handle(self, command: CloseOpenShiftsCommand) -> None:
        now = self._time_provider.now()
        cutoff = now - timedelta(hours=command.close_after_hours)
        async with UnitOfWork() as session:
            shifts = await self._shift_repository.get_open_started_at_or_before(
                session,
                cutoff,
            )

            for shift in shifts:
                shift.automatically_close(now)
                await self._shift_repository.save(session, shift)
                await self.save_events(session, shift.pull_events())

        logger.info(
            "Close open shifts command completed closed_count={} cutoff={}",
            len(shifts),
            cutoff,
        )
