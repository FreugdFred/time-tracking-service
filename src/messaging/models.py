import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Uuid, func, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base import Base


class DbEvent(Base):
    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    type: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))

    data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )