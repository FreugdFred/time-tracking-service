from dependency_container import Dependency
from src.core.settings import Settings
from src.domains.shifts.commands.close_open_shifts.command import (
    CloseOpenShiftsCommand,
)
from src.domains.shifts.commands.close_open_shifts.handler import (
    CloseOpenShiftsCommandHandler,
)


async def close_open_shifts() -> None:
    settings = Dependency.get(Settings)
    handler = Dependency.get(CloseOpenShiftsCommandHandler)
    await handler.handle(
        CloseOpenShiftsCommand(
            close_after_hours=settings.SHIFT_AUTO_CLOSE_AFTER_HOURS,
        )
    )
