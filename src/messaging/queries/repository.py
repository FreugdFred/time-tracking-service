from dependency_container import Dependency
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.messaging.entity import EventEnvelope
from src.messaging.mapper import MessagingMapper
from src.messaging.models import DbEvent


class QueryMessagingRepository:
    async def list_unpublished(self, amount: int = 100) -> list[EventEnvelope]:
        query = (
            select(DbEvent)
            .where(DbEvent.published_at.is_(None))
            .order_by(DbEvent.occurred_at.asc(), DbEvent.id.asc())
            .limit(amount)
        )

        async with Dependency.get(AsyncSession) as session:
            result = await session.scalars(query)
            return [MessagingMapper.to_domain(event) for event in result.all()]
