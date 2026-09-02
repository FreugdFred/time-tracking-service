from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from src.core.schema_types import UtcDateTimeInput


class SavePauseInput(BaseModel):
    id: UUID
    shift_id: UUID | None = None
    started_at: UtcDateTimeInput | None = None
    finished_at: UtcDateTimeInput | None = None

    @model_validator(mode="after")
    def validate_pause(self) -> Self:
        if (
            self.started_at is not None
            and self.finished_at is not None
            and self.finished_at <= self.started_at
        ):
            raise ValueError("finished_at must be after started_at")

        return self
