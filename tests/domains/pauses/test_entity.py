from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.domains.pauses.entity import PauseEntity
from src.domains.pauses.events import (
    PauseDeletedEvent,
    PauseFinishedEvent,
    PauseFinishChangedEvent,
    PauseStartedEvent,
    PauseStartChangedEvent,
)
from src.domains.shifts.entity import ShiftEntity
from src.exceptions import (
    AlreadyFinishedException,
    InvalidTimeRangeException,
    UnfinishedException,
)
from time_provider import FakeTimeProvider


@pytest.fixture
def now(time_provider: FakeTimeProvider) -> datetime:
    current_time = datetime(2026, 9, 2, 10, tzinfo=UTC)
    time_provider.travel(current_time)
    return current_time


def test_finish_sets_end_time_and_cannot_run_twice(
    now: datetime,
    time_provider: FakeTimeProvider,
) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=now - timedelta(hours=1),
    )

    pause.finish()

    assert pause.finished_at == now
    assert pause.is_finished
    with pytest.raises(AlreadyFinishedException):
        pause.finish()


def test_finish_rejects_non_positive_duration(
    now: datetime,
    time_provider: FakeTimeProvider,
) -> None:
    pause = PauseEntity(shift_id=uuid4(), started_at=now)

    with pytest.raises(InvalidTimeRangeException):
        pause.finish()


def test_finished_pause_can_change_its_complete_time_range(now: datetime) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=now - timedelta(hours=2),
        finished_at=now - timedelta(hours=1),
    )
    new_started_at = now - timedelta(minutes=45)
    new_finished_at = now - timedelta(minutes=15)

    pause.change_time_range(
        started_at=new_started_at,
        finished_at=new_finished_at,
    )

    assert pause.started_at == new_started_at
    assert pause.finished_at == new_finished_at


def test_active_pause_cannot_be_edited(now: datetime) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=now - timedelta(hours=1),
    )

    with pytest.raises(UnfinishedException):
        pause.change_started_at(now - timedelta(minutes=30))
    with pytest.raises(UnfinishedException):
        pause.change_finished_at(now)


def test_edit_rejects_invalid_time_range(now: datetime) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=now - timedelta(hours=2),
        finished_at=now - timedelta(hours=1),
    )

    with pytest.raises(InvalidTimeRangeException):
        pause.change_time_range(started_at=now, finished_at=now)


def test_shift_records_pause_lifecycle_events(
    now: datetime,
    time_provider: FakeTimeProvider,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=now - timedelta(hours=2),
    )

    pause = shift.start_pause()
    time_provider.travel(now + timedelta(minutes=30))
    shift.finish_pause()

    assert shift.pull_events() == (
        PauseStartedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            pause_id=pause.id,
            started_at=now,
            occurrence_datetime=now,
        ),
        PauseFinishedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            pause_id=pause.id,
            finished_at=now + timedelta(minutes=30),
            occurrence_datetime=now + timedelta(minutes=30),
        ),
    )


def test_shift_records_changed_pause_fields(
    now: datetime,
    time_provider: FakeTimeProvider,
) -> None:
    previous_started_at = now - timedelta(hours=2)
    previous_finished_at = now - timedelta(hours=1)
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=previous_started_at,
        finished_at=previous_finished_at,
    )
    shift = ShiftEntity(
        id=pause.shift_id,
        reference_id="employee-1",
        started_at=now - timedelta(hours=3),
        finished_at=now,
        pauses=[pause],
    )
    started_at = previous_started_at + timedelta(minutes=15)
    finished_at = previous_finished_at + timedelta(minutes=15)

    shift.change_pause_time_range(
        pause.id,
        started_at=started_at,
        finished_at=finished_at,
    )

    assert shift.pull_events() == (
        PauseStartChangedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            pause_id=pause.id,
            previous_started_at=previous_started_at,
            started_at=started_at,
            occurrence_datetime=now,
        ),
        PauseFinishChangedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            pause_id=pause.id,
            previous_finished_at=previous_finished_at,
            finished_at=finished_at,
            occurrence_datetime=now,
        ),
    )


def test_shift_records_pause_deletion(
    now: datetime,
    time_provider: FakeTimeProvider,
) -> None:
    pause = PauseEntity(
        shift_id=uuid4(),
        started_at=now - timedelta(hours=2),
        finished_at=now - timedelta(hours=1),
    )
    shift = ShiftEntity(
        id=pause.shift_id,
        reference_id="employee-1",
        started_at=now - timedelta(hours=3),
        finished_at=now,
        pauses=[pause],
    )

    shift.delete_pause(pause.id)

    assert shift.pull_events() == (
        PauseDeletedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            pause_id=pause.id,
            occurrence_datetime=now,
        ),
    )
