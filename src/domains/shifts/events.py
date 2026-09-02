from datetime import datetime
from uuid import UUID

from src.core.events import DomainEvent


class ShiftEvent(DomainEvent):
    shift_id: UUID


class ShiftStartedEvent(ShiftEvent):
    started_at: datetime


class ShiftFinishedEvent(ShiftEvent):
    finished_at: datetime


class ShiftStartChangedEvent(ShiftEvent):
    previous_started_at: datetime
    started_at: datetime


class ShiftFinishChangedEvent(ShiftEvent):
    previous_finished_at: datetime
    finished_at: datetime


class ShiftApprovedEvent(ShiftEvent):
    pass


class ShiftRejectedEvent(ShiftEvent):
    pass


class ShiftAutomaticallyClosedEvent(ShiftEvent):
    pass


class ShiftDeletedEvent(ShiftEvent):
    pass
