from collections.abc import Iterable

from dependency_container import Dependency
from sqlalchemy.ext.asyncio import AsyncSession

from src.messaging.command_repository import CommandMessagingRepository
from src.messaging.entity import BaseDomainEvent


class HandlerBase:
    @staticmethod
    async def save_events(
        session: AsyncSession,
        events: Iterable[BaseDomainEvent],
    ) -> None:
        repository = Dependency.get(CommandMessagingRepository)
        await repository.save_many(session, events)
