from uuid import UUID

from fastapi import APIRouter

from dependency_container import Dependency
from src.domains.pauses.commands.clock_pause.command import ClockPauseCommand
from src.domains.pauses.commands.clock_pause.handler import ClockPauseCommandHandler
from src.domains.pauses.commands.remove_pause.command import RemovePauseCommand
from src.domains.pauses.commands.remove_pause.handler import RemovePauseCommandHandler
from src.domains.pauses.commands.save_pause.command import SavePauseCommand
from src.domains.pauses.commands.save_pause.handler import SavePauseCommandHandler
from src.domains.pauses.queries.get_pause_by_id.handler import (
    GetPauseByIdQueryHandler,
)
from src.domains.pauses.queries.get_pause_by_id.query import GetPauseByIdQuery
from src.domains.pauses.query_models import PauseQueryModel
from src.domains.pauses.schemas import SavePauseInput

pause_router = APIRouter(prefix="/pause", tags=["pause"])


@pause_router.post("/clock")
async def clock_pause(reference_id: str) -> UUID:
    handler = Dependency.get(ClockPauseCommandHandler)
    return await handler.handle(ClockPauseCommand(reference_id=reference_id))


@pause_router.post("/save")
async def save_pause(input: SavePauseInput) -> None:
    handler = Dependency.get(SavePauseCommandHandler)
    await handler.handle(
        SavePauseCommand(
            id=input.id,
            shift_id=input.shift_id,
            started_at=input.started_at,
            finished_at=input.finished_at,
        )
    )


@pause_router.delete("/remove")
async def remove_pause(id: UUID) -> None:
    handler = Dependency.get(RemovePauseCommandHandler)
    await handler.handle(RemovePauseCommand(id=id))


@pause_router.get("/{id}", response_model=PauseQueryModel)
async def get_pause(id: UUID) -> PauseQueryModel:
    handler = Dependency.get(GetPauseByIdQueryHandler)
    return await handler.handle(GetPauseByIdQuery(id=id))
