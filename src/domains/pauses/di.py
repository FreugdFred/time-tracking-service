from dependency_container import Dependency
from src.domains.pauses.commands.clock_pause.handler import ClockPauseCommandHandler
from src.domains.pauses.commands.remove_pause.handler import RemovePauseCommandHandler
from src.domains.pauses.commands.save_pause.handler import SavePauseCommandHandler
from src.domains.pauses.queries.get_pause_by_id.handler import (
    GetPauseByIdQueryHandler,
)
from src.domains.pauses.query_repository import QueryPauseRepository


def include_pause_dependencies() -> None:
    Dependency.register(QueryPauseRepository, QueryPauseRepository)

    Dependency.register(ClockPauseCommandHandler, ClockPauseCommandHandler)
    Dependency.register(RemovePauseCommandHandler, RemovePauseCommandHandler)
    Dependency.register(SavePauseCommandHandler, SavePauseCommandHandler)

    Dependency.register(GetPauseByIdQueryHandler, GetPauseByIdQueryHandler)
