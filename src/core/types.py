from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.engine import Dialect
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import TypeDecorator


class TimezoneAwareDateTime(TypeDecorator[datetime]):
    """Store aware UTC datetimes consistently across supported databases."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String())
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | str | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")

        value = value.astimezone(UTC)
        return value.isoformat() if dialect.name == "sqlite" else value

    def process_result_value(
        self,
        value: datetime | str | None,
        dialect: Dialect,
    ) -> datetime | None:
        del dialect
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None or value.utcoffset() is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
