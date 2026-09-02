from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

QueryModel = TypeVar("QueryModel")


class PaginatedQueryModel(BaseModel, Generic[QueryModel]):
    items: list[QueryModel]
    total: int
    limit: int
    offset: int


class ShiftPauseQueryModel(BaseModel):
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ShiftByReferenceIdQueryModel(BaseModel):
    started_at: datetime
    finished_at: datetime | None
    pauses: list[ShiftPauseQueryModel]
    automatically_closed: bool
    approved: bool

    model_config = ConfigDict(from_attributes=True)


class ShiftQueryModel(ShiftByReferenceIdQueryModel):
    reference_id: str
