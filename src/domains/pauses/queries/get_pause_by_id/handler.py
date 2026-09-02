from loguru import logger

from src.domains.pauses.queries.get_pause_by_id.query import GetPauseByIdQuery
from src.domains.pauses.query_models import PauseQueryModel
from src.domains.pauses.query_repository import QueryPauseRepository
from src.exceptions import NotFoundException

class GetPauseByIdQueryHandler:
    def __init__(self, repository: QueryPauseRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetPauseByIdQuery) -> PauseQueryModel:
        output = await self._repository.get(query.id)
        if output is None:
            logger.warning("Pause query returned no result pause_id={}", query.id)
            raise NotFoundException(PauseQueryModel, str(query.id))

        logger.debug("Pause query completed pause_id={}", query.id)
        return output
