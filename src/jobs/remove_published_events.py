from dependency_container import Dependency

from src.core.settings import Settings
from src.messaging.commands.remove_published_events.command import (
    RemovePublishedEventsCommand,
)
from src.messaging.commands.remove_published_events.handler import (
    RemovePublishedEventsCommandHandler,
)


async def remove_published_events() -> None:
    settings = Dependency.get(Settings)
    handler = Dependency.get(RemovePublishedEventsCommandHandler)
    await handler.handle(
        RemovePublishedEventsCommand(
            retention_minutes=settings.EVENT_RETENTION_MINUTES,
        )
    )
