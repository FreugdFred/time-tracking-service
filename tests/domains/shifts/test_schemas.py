from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domains.shifts.schemas import DateRangeInput, SaveShiftInput


def test_reference_id_accepts_255_characters() -> None:
    value = "é" * 255
    assert SaveShiftInput(id=uuid4(), reference_id=value).reference_id == value


def test_reference_id_rejects_256_characters() -> None:
    with pytest.raises(ValidationError, match="255"):
        SaveShiftInput(id=uuid4(), reference_id="x" * 256)


def test_save_shift_input_defaults_upsert_booleans_to_none() -> None:
    input = SaveShiftInput(id=uuid4())

    assert input.approved is None
    assert input.automatically_closed is None


def test_save_shift_input_treats_naive_datetimes_as_local_time() -> None:
    input = SaveShiftInput(
        id=uuid4(),
        started_at=datetime(2026, 9, 3, 10),
        finished_at=datetime(2026, 9, 3, 17),
    )

    assert input.started_at == datetime(2026, 9, 3, 8, tzinfo=UTC)
    assert input.finished_at == datetime(2026, 9, 3, 15, tzinfo=UTC)


def test_date_range_input_converts_explicit_offsets_to_utc() -> None:
    utc_plus_two = timezone(timedelta(hours=2))

    input = DateRangeInput(
        start=datetime(2026, 9, 3, 10, tzinfo=utc_plus_two),
        end=datetime(2026, 9, 3, 17, tzinfo=utc_plus_two),
    )

    assert input.start == datetime(2026, 9, 3, 8, tzinfo=UTC)
    assert input.end == datetime(2026, 9, 3, 15, tzinfo=UTC)
