from typing import Literal

from pydantic import BaseModel, Field, NonNegativeInt


class GetShiftsByReferenceIdQuery(BaseModel):
    reference_id: str
    approved: bool | None = None
    automatically_closed: bool | None = None
    is_open: bool | None = None
    sort_direction: Literal["asc", "desc"] = "desc"
    limit: NonNegativeInt = Field(le=100)
    offset: NonNegativeInt
