from dependency_container import Dependency

from src.messaging.command_repository import CommandMessagingRepository
from src.messaging.commands.remove_published_events.handler import (
    RemovePublishedEventsCommandHandler,
)
from src.messaging.event_publisher import EventPublisher
from src.messaging.query_repository import QueryMessagingRepository


def include_messaging_dependencies() -> None:
    Dependency.register(CommandMessagingRepository, CommandMessagingRepository)
    Dependency.register(QueryMessagingRepository, QueryMessagingRepository)
    Dependency.register(EventPublisher, EventPublisher)
    Dependency.register(RemovePublishedEventsCommandHandler,RemovePublishedEventsCommandHandler,
    )
