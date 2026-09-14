from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.messaging.entity import BaseDomainEvent
from src.messaging.mapper import MessagingMapper
from src.messaging.models import DbEvent


class CommandMessagingRepository:
    async def set_publish(self, session: AsyncSession, id: UUID) -> None:
        query = (
            update(DbEvent)
            .where(DbEvent.id == id)
            .values(published_at=func.now())
        )

        await session.execute(query)

    async def save_many(
        self,
        session: AsyncSession,
        events: Iterable[BaseDomainEvent],
    ) -> None:
        db_events = [MessagingMapper.from_domain(event) for event in events]
        session.add_all(db_events)
