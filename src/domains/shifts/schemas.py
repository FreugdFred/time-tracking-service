from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from pydantic.types import NonNegativeInt

class DateRangeInput(BaseModel):
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start > self.end:
            raise ValueError("start must be before to_datetime")
        return self


class SaveShiftInput(BaseModel):
    id: UUID
    reference_id: str | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None

    automatically_closed: bool = False
    approved: bool = False

    @model_validator(mode="after")
    def validate_shift(self) -> Self:
        if (
            self.started_at is not None
            and self.finished_at is not None
            and self.finished_at <= self.started_at
        ):
            raise ValueError("finished_at must be after started_at")

        return self


class PaginationInput(BaseModel):
    limit: NonNegativeInt = Field(default=10, le=100)
    offset: NonNegativeInt = Field(default=0)


class ShiftFiltersInput(BaseModel):
    approved: bool | None = None
    automatically_closed: bool | None = None
    is_open: bool | None = None
    sort_direction: Literal["asc", "desc"] = "desc"
