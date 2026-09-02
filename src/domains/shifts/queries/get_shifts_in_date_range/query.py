from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, NonNegativeInt, model_validator


class GetShiftsInDateRangeQuery(BaseModel):
    reference_id: str | None = None
    start: datetime
    end: datetime
    approved: bool | None = None
    automatically_closed: bool | None = None
    is_open: bool | None = None
    sort_direction: Literal["asc", "desc"] = "desc"

    limit: NonNegativeInt = Field(le=100)
    offset: NonNegativeInt

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start > self.end:
            raise ValueError("start must be before end")
        return self
