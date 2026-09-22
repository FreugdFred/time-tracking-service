from typing import Literal

from pydantic import BaseModel, Field, NonNegativeInt

from src.core.schema_types import ReferenceId


class GetShiftsByReferenceIdQuery(BaseModel):
    reference_id: ReferenceId
    approved: bool | None = None
    automatically_closed: bool | None = None
    is_open: bool | None = None
    sort_direction: Literal["asc", "desc"] = "desc"
    limit: NonNegativeInt = Field(le=100)
    offset: NonNegativeInt
