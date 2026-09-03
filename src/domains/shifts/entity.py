from __future__ import annotations

from datetime import datetime, timedelta
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator, validate_call

from src.core.events import DomainEvent
from src.domains.pauses.entity import PauseEntity
from src.domains.pauses.events import (
    PauseDeletedEvent,
    PauseFinishedEvent,
    PauseFinishChangedEvent,
    PauseStartedEvent,
    PauseStartChangedEvent,
)
from src.domains.shifts.events import (
    ShiftApprovedEvent,
    ShiftAutomaticallyClosedEvent,
    ShiftCreatedEvent,
    ShiftDeletedEvent,
    ShiftFinishedEvent,
    ShiftFinishChangedEvent,
    ShiftRejectedEvent,
    ShiftStartedEvent,
    ShiftStartChangedEvent,
)
from src.exceptions import (
    AlreadyActiveException,
    AlreadyFinishedException,
    InvalidTimeRangeException,
    NotFoundException,
    OverlappingException,
    UnfinishedException,
)

class Shift(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    reference_id: str

    started_at: datetime
    finished_at: datetime | None = None

    automatically_closed: bool = False
    approved: bool = False

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_finished_at(self) -> Self:
        if self.finished_at is not None and self.finished_at <= self.started_at:
            raise ValueError("finished_at must be after started_at")

        return self

    def __lt__(self, other: Self) -> bool:
        if self.started_at != other.started_at:
            return self.started_at > other.started_at

        return str(self.id) < str(other.id)


def _empty_pauses() -> list[PauseEntity]:
    return []


class ShiftEntity(Shift):
    pauses: list[PauseEntity] = Field(default_factory=_empty_pauses)
    _events: list[DomainEvent] = PrivateAttr(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        reference_id: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        automatically_closed: bool = False,
        approved: bool = False,
    ) -> Self:
        shift = cls(
            id=id,
            reference_id=reference_id,
            started_at=started_at,
            finished_at=finished_at,
            automatically_closed=automatically_closed,
            approved=approved,
        )
        shift._record_event(
            ShiftCreatedEvent(
                reference_id=shift.reference_id,
                shift_id=shift.id,
                started_at=shift.started_at,
                finished_at=shift.finished_at,
                automatically_closed=shift.automatically_closed,
                approved=shift.approved,
            )
        )
        return shift

    @classmethod
    def start(cls, reference_id: str, started_at: datetime) -> Self:
        shift = cls.create(
            id=uuid4(),
            reference_id=reference_id,
            started_at=started_at,
        )
        shift._record_event(
            ShiftStartedEvent(
                reference_id=shift.reference_id,
                shift_id=shift.id,
                started_at=shift.started_at,
            )
        )
        return shift

    def pull_events(self) -> tuple[DomainEvent, ...]:
        events = tuple(self._events)
        self._events.clear()
        return events

    def delete(self) -> None:
        self._record_event(
            ShiftDeletedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
            )
        )

    def total_worked_hours(self, at: datetime) -> float:
        finished_at = self.finished_at or at
        worked_time = finished_at - self.started_at

        for pause in self.pauses:
            pause_finished_at = pause.finished_at or at
            worked_time -= pause_finished_at - pause.started_at

        return worked_time.total_seconds() / timedelta(hours=1).total_seconds()

    @property
    def is_finished(self) -> bool:
        return bool(self.finished_at)

    @property
    def active_pause(self) -> PauseEntity | None:
        return next((p for p in self.pauses if not p.is_finished), None)

    @property
    def latest_pause(self) -> PauseEntity | None:
        if not self.pauses:
            return None

        return max(self.pauses, key=lambda pause: pause.started_at)

    @property
    def first_pause(self) -> PauseEntity | None:
        if not self.pauses:
            return None

        return min(self.pauses, key=lambda pause: pause.started_at)

    def get_pause(self, pause_id: UUID) -> PauseEntity:
        pause = next((p for p in self.pauses if p.id == pause_id), None)
        if pause is None:
            raise NotFoundException(PauseEntity, str(pause_id))

        return pause

    def delete_pause(self, pause_id: UUID) -> None:
        pause = self.get_pause(pause_id)
        self.pauses.remove(pause)
        self._record_event(
            PauseDeletedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
                pause_id=pause.id,
            )
        )

    def start_pause(self, started_at: datetime) -> PauseEntity:
        if self.active_pause:
            raise AlreadyActiveException(PauseEntity, str(self.id))

        elif self.is_finished:
            raise AlreadyFinishedException(ShiftEntity, str(self.id))

        new_pause = PauseEntity(shift_id=self.id, started_at=started_at)

        self.pauses.append(new_pause)
        self._record_event(
            PauseStartedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
                pause_id=new_pause.id,
                started_at=new_pause.started_at,
            )
        )
        return new_pause

    def finish_pause(self, finished_at: datetime) -> PauseEntity:
        active_pause = self.active_pause
        if not active_pause:
            raise NotFoundException(PauseEntity)

        active_pause.finish(finished_at)
        assert active_pause.finished_at is not None
        self._record_event(
            PauseFinishedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
                pause_id=active_pause.id,
                finished_at=active_pause.finished_at,
            )
        )
        return active_pause

    @validate_call
    def add_pause(self, new_pause: PauseEntity) -> PauseEntity:
        if not self.is_finished:
            raise UnfinishedException(ShiftEntity, str(self.id))

        if not new_pause.is_finished:
            raise UnfinishedException(PauseEntity, str(new_pause.id))

        assert new_pause.finished_at
        if self.overlaps_other_pause(
            new_pause.id,
            started_at=new_pause.started_at,
            finished_at=new_pause.finished_at,
        ):
            raise OverlappingException(
                ShiftEntity,
                identifier=str(self.id),
                start=new_pause.started_at,
                end=new_pause.finished_at,
            )

        assert self.finished_at
        if not self.started_at <= new_pause.started_at < self.finished_at:
            raise InvalidTimeRangeException(
                ShiftEntity,
                identifier=str(self.id),
                start=new_pause.started_at,
                end=self.finished_at,
                detail="started_at must be in range of the shift",
            )

        assert new_pause.finished_at
        if not new_pause.started_at < new_pause.finished_at <= self.finished_at:
            raise InvalidTimeRangeException(
                ShiftEntity,
                identifier=str(self.id),
                start=new_pause.started_at,
                end=new_pause.finished_at,
                detail="finished_at must be in range of the shift",
            )

        self.pauses.append(new_pause)
        return new_pause

    def finish(self, finished_at: datetime) -> None:
        if self.is_finished:
            raise AlreadyFinishedException(ShiftEntity, str(self.id))

        if finished_at <= self.started_at:
            raise InvalidTimeRangeException(
                ShiftEntity,
                identifier=str(self.id),
                start=self.started_at,
                end=finished_at,
                detail="finished_at must be after started_at",
            )

        for pause in filter(lambda p: not p.is_finished, self.pauses):
            pause.finish(finished_at)
            assert pause.finished_at is not None
            self._record_event(
                PauseFinishedEvent(
                    reference_id=self.reference_id,
                    shift_id=self.id,
                    pause_id=pause.id,
                    finished_at=pause.finished_at,
                )
            )

        self.finished_at = finished_at
        self._record_event(
            ShiftFinishedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
                finished_at=finished_at,
            )
        )

    def automatically_close(self, finished_at: datetime) -> None:
        self.finish(finished_at)
        self.automatically_closed = True
        self._record_event(
            ShiftAutomaticallyClosedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
            )
        )

    def change_finished_at(self, new_finished_at: datetime) -> None:
        self.change_time_range(finished_at=new_finished_at)

    def change_started_at(self, new_started_at: datetime) -> None:
        self.change_time_range(started_at=new_started_at)

    def change_time_range(
        self,
        *,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        if not self.is_finished:
            raise UnfinishedException(ShiftEntity, str(self.id))

        new_started_at = started_at if started_at is not None else self.started_at
        assert self.finished_at is not None
        new_finished_at = (
            finished_at if finished_at is not None else self.finished_at
        )

        if new_finished_at <= new_started_at:
            raise OverlappingException(
                ShiftEntity,
                identifier=str(self.id),
                start=new_started_at,
                end=new_finished_at,
            )

        first_pause = self.first_pause
        if first_pause is not None and new_started_at > first_pause.started_at:
            raise OverlappingException(
                ShiftEntity,
                identifier=str(self.id),
                start=new_started_at,
                end=first_pause.started_at,
            )

        latest_pause = self.latest_pause
        if (
            latest_pause is not None
            and latest_pause.finished_at is not None
            and latest_pause.finished_at > new_finished_at
        ):
            raise OverlappingException(
                ShiftEntity,
                identifier=str(self.id),
                start=new_started_at,
                end=new_finished_at,
            )

        previous_started_at = self.started_at
        previous_finished_at = self.finished_at

        self.started_at = new_started_at
        self.finished_at = new_finished_at

        if new_started_at != previous_started_at:
            self._record_event(
                ShiftStartChangedEvent(
                    reference_id=self.reference_id,
                    shift_id=self.id,
                    previous_started_at=previous_started_at,
                    started_at=new_started_at,
                )
            )

        if new_finished_at != previous_finished_at:
            self._record_event(
                ShiftFinishChangedEvent(
                    reference_id=self.reference_id,
                    shift_id=self.id,
                    previous_finished_at=previous_finished_at,
                    finished_at=new_finished_at,
                )
            )

    def change_pause_started_at(self, pause_id: UUID, started_at: datetime) -> None:
        pause = self.get_pause(pause_id)
        if pause.finished_at is None:
            raise UnfinishedException(PauseEntity, str(pause.id))

        self.change_pause_time_range(
            pause_id,
            started_at=started_at,
            finished_at=pause.finished_at,
        )

    def change_pause_finished_at(self, pause_id: UUID, finished_at: datetime) -> None:
        pause = self.get_pause(pause_id)
        self.change_pause_time_range(
            pause_id,
            started_at=pause.started_at,
            finished_at=finished_at,
        )

    def change_pause_time_range(
        self,
        pause_id: UUID,
        *,
        started_at: datetime,
        finished_at: datetime,
    ) -> None:
        pause = self.get_pause(pause_id)

        if not self.is_finished:
            raise UnfinishedException(ShiftEntity, str(self.id))

        if self.overlaps_other_pause(
            pause_id,
            started_at=started_at,
            finished_at=finished_at,
        ):
            raise OverlappingException(
                ShiftEntity,
                identifier=str(self.id),
                start=started_at,
                end=finished_at,
            )

        assert self.finished_at
        if not self.started_at <= started_at < self.finished_at:
            raise InvalidTimeRangeException(
                ShiftEntity,
                identifier=str(self.id),
                start=started_at,
                end=self.finished_at,
                detail="started_at must be in range of the shift",
            )

        if not started_at < finished_at <= self.finished_at:
            raise InvalidTimeRangeException(
                ShiftEntity,
                identifier=str(self.id),
                start=started_at,
                end=finished_at,
                detail="finished_at must be in range of the shift",
            )

        previous_started_at = pause.started_at
        previous_finished_at = pause.finished_at

        pause.change_time_range(started_at=started_at, finished_at=finished_at)

        if started_at != previous_started_at:
            self._record_event(
                PauseStartChangedEvent(
                    reference_id=self.reference_id,
                    shift_id=self.id,
                    pause_id=pause.id,
                    previous_started_at=previous_started_at,
                    started_at=started_at,
                )
            )

        if finished_at != previous_finished_at:
            assert previous_finished_at is not None
            self._record_event(
                PauseFinishChangedEvent(
                    reference_id=self.reference_id,
                    shift_id=self.id,
                    pause_id=pause.id,
                    previous_finished_at=previous_finished_at,
                    finished_at=finished_at,
                )
            )

    def overlaps_other_pause(
        self,
        pause_id: UUID,
        *,
        started_at: datetime,
        finished_at: datetime,
    ) -> bool:
        return any(
            started_at < pause.finished_at and finished_at > pause.started_at
            for pause in self.pauses
            if pause.id != pause_id and pause.finished_at is not None
        )

    def approve(self) -> None:
        if not self.is_finished:
            raise UnfinishedException(ShiftEntity, str(self.id))

        if self.approved:
            return

        self.approved = True
        self._record_event(
            ShiftApprovedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
            )
        )

    def disapprove(self) -> None:
        if not self.is_finished:
            raise UnfinishedException(ShiftEntity, str(self.id))

        if not self.approved:
            return

        self.approved = False
        self._record_event(
            ShiftRejectedEvent(
                reference_id=self.reference_id,
                shift_id=self.id,
            )
        )

    def _record_event(self, event: DomainEvent) -> None:
        self._events.append(event)
