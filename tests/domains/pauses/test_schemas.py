from datetime import UTC, datetime
from uuid import uuid4

from src.domains.pauses.schemas import SavePauseInput


def test_save_pause_input_treats_naive_datetimes_as_local_time() -> None:
    input = SavePauseInput(
        id=uuid4(),
        started_at=datetime(2026, 9, 3, 12),
        finished_at=datetime(2026, 9, 3, 13),
    )

    assert input.started_at == datetime(2026, 9, 3, 10, tzinfo=UTC)
    assert input.finished_at == datetime(2026, 9, 3, 11, tzinfo=UTC)
