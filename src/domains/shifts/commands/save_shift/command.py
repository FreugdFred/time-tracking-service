from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator



class SaveShiftCommand(BaseModel):
    id: UUID
    reference_id: str | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None

    automatically_closed: bool = False
    approved: bool = False

    @property
    def is_time_set(self) -> bool:
        return self.started_at is not None and self.finished_at is not None

    @model_validator(mode="after")
    def validate_shift(self) -> Self:
        if (
            self.started_at is not None
            and self.finished_at is not None
            and self.finished_at <= self.started_at
        ):
            raise ValueError("finished_at must be after started_at")

        return self
