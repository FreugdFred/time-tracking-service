from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base
from src.core.mixins import TimestampMixin
from src.core.types import TimezoneAwareDateTime

if TYPE_CHECKING:
    from src.domains.shifts.models import DbShift


class DbPause(Base, TimestampMixin):
    """Model for user pauses in shifts."""

    __tablename__ = "pause"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(
        TimezoneAwareDateTime(), nullable=False
    )
    finished_at: Mapped[datetime] = mapped_column(
        TimezoneAwareDateTime(), nullable=True
    )

    shift_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("shift.id"), nullable=False
    )
    shift: Mapped["DbShift"] = relationship(back_populates="pauses")

    __table_args__ = (
        CheckConstraint(
            "(finished_at IS NULL) OR (started_at < finished_at)",
            name="check_started_before_finished",
        ),
    )
