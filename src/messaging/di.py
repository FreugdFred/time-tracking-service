from dependency_container import Dependency

from messaging.commands.repository import CommandMessagingRepository
from src.messaging.commands.remove_published_events.handler import (
    RemovePublishedEventsCommandHandler,
)
from src.messaging.event_publisher import EventPublisher
from messaging.queries.repository import QueryMessagingRepository


def include_messaging_dependencies() -> None:
    Dependency.register(CommandMessagingRepository, CommandMessagingRepository)
    Dependency.register(QueryMessagingRepository, QueryMessagingRepository)
    Dependency.register(EventPublisher, EventPublisher)
    Dependency.register(RemovePublishedEventsCommandHandler,RemovePublishedEventsCommandHandler,
    )
