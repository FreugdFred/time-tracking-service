from datetime import datetime
from uuid import UUID

from src.core.events import DomainEvent


class PauseEvent(DomainEvent):
    shift_id: UUID
    pause_id: UUID


class PauseStartedEvent(PauseEvent):
    started_at: datetime


class PauseFinishedEvent(PauseEvent):
    finished_at: datetime


class PauseStartChangedEvent(PauseEvent):
    previous_started_at: datetime
    started_at: datetime


class PauseFinishChangedEvent(PauseEvent):
    previous_finished_at: datetime
    finished_at: datetime


class PauseDeletedEvent(PauseEvent):
    pass
