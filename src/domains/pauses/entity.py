from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.exceptions import (
    AlreadyFinishedException,
    InvalidTimeRangeException,
    UnfinishedException,
)


class Pause(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    shift_id: UUID

    started_at: datetime
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_finished_at(self) -> Self:
        if self.finished_at is not None and self.finished_at <= self.started_at:
            raise ValueError("finished_at must be after started_at")

        return self


class PauseEntity(Pause):
    @property
    def is_finished(self) -> bool:
        return bool(self.finished_at)

    def finish(self, finished_at: datetime) -> None:
        if self.is_finished:
            raise AlreadyFinishedException(PauseEntity, str(self.id))

        if finished_at <= self.started_at:
            raise InvalidTimeRangeException(
                PauseEntity,
                identifier=str(self.id),
                start=self.started_at,
                end=finished_at,
                detail="finished_at must be after started_at",
            )

        self.finished_at = finished_at

    def change_started_at(self, started_at: datetime) -> None:
        if self.finished_at is None:
            raise UnfinishedException(PauseEntity, identifier=str(self.id))

        self.change_time_range(started_at=started_at, finished_at=self.finished_at)

    def change_finished_at(self, finished_at: datetime) -> None:
        self.change_time_range(started_at=self.started_at, finished_at=finished_at)

    def change_time_range(
        self,
        *,
        started_at: datetime,
        finished_at: datetime,
    ) -> None:
        if not self.is_finished:
            raise UnfinishedException(
                PauseEntity,
                identifier=str(self.id),
            )

        if finished_at <= started_at:
            raise InvalidTimeRangeException(
                PauseEntity,
                identifier=str(self.id),
                start=started_at,
                end=finished_at,
                detail="finished_at must be after started_at",
            )

        self.started_at = started_at
        self.finished_at = finished_at
