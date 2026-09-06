from datetime import datetime
from uuid import UUID

from messaging.entity import BaseDomainEvent


class PauseEventBase(BaseDomainEvent):
    shift_id: UUID
    pause_id: UUID


class PauseStartedEvent(PauseEventBase):
    started_at: datetime


class PauseFinishedEvent(PauseEventBase):
    finished_at: datetime


class PauseStartChangedEvent(PauseEventBase):
    previous_started_at: datetime
    started_at: datetime


class PauseFinishChangedEvent(PauseEventBase):
    previous_finished_at: datetime
    finished_at: datetime


class PauseDeletedEvent(PauseEventBase):
    pass
