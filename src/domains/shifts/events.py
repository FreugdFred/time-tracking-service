from datetime import datetime
from uuid import UUID

from messaging.entity import BaseDomainEvent


class ShiftEventBase(BaseDomainEvent):
    shift_id: UUID


class ShiftCreatedEvent(ShiftEventBase):
    started_at: datetime
    finished_at: datetime | None
    automatically_closed: bool
    approved: bool


class ShiftStartedEvent(ShiftEventBase):
    started_at: datetime


class ShiftFinishedEvent(ShiftEventBase):
    finished_at: datetime


class ShiftStartChangedEvent(ShiftEventBase):
    previous_started_at: datetime
    started_at: datetime


class ShiftFinishChangedEvent(ShiftEventBase):
    previous_finished_at: datetime
    finished_at: datetime


class ShiftApprovedEvent(ShiftEventBase):
    pass


class ShiftRejectedEvent(ShiftEventBase):
    pass


class ShiftAutomaticallyClosedEvent(ShiftEventBase):
    pass


class ShiftDeletedEvent(ShiftEventBase):
    pass
