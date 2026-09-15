from collections.abc import Iterable

from dependency_container import Dependency
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import Settings
from messaging.commands.repository import CommandMessagingRepository
from src.messaging.entity import BaseDomainEvent


class HandlerBase:
    @staticmethod
    async def save_events(
        session: AsyncSession,
        events: Iterable[BaseDomainEvent],
    ) -> None:
        if Dependency.get(Settings).NATS_URL is None:
            return

        repository = Dependency.get(CommandMessagingRepository)
        await repository.save_many(session, events)
