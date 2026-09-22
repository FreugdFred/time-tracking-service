from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from dependency_container import Dependency
from src.domains.pauses.models import DbPause
from src.domains.pauses.query_models import PauseQueryModel


class QueryPauseRepository:
    async def get(self, id: UUID) -> PauseQueryModel | None:
        async with Dependency.get(AsyncSession) as session:
            db_pause = await session.get(DbPause, id)
            return PauseQueryModel.model_validate(db_pause) if db_pause else None
