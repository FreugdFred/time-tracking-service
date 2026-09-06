from dependency_container import Dependency

from messaging.event_publisher import EventPublisher
from messaging.repository import MessagingRepository


def include_messaging_dependencies() -> None:
    Dependency.register_factory(EventPublisher, EventPublisher)
    Dependency.register(MessagingRepository, EventPublisher)