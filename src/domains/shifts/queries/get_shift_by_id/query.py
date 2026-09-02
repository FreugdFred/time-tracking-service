from uuid import UUID

from pydantic import BaseModel


class GetShiftByIdQuery(BaseModel):
    id: UUID
