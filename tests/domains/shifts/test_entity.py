from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.domains.pauses.entity import PauseEntity
from src.domains.shifts.entity import ShiftEntity
from src.domains.shifts.events import (
    ShiftApprovedEvent,
    ShiftAutomaticallyClosedEvent,
    ShiftDeletedEvent,
    ShiftFinishedEvent,
    ShiftFinishChangedEvent,
    ShiftRejectedEvent,
    ShiftStartedEvent,
    ShiftStartChangedEvent,
)
from src.exceptions import (
    AlreadyActiveException,
    AlreadyFinishedException,
    InvalidTimeRangeException,
    NotFoundException,
    OverlappingException,
    UnfinishedException,
)
from time_provider import FakeTimeProvider


NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


def _finished_shift() -> ShiftEntity:
    return ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 17, tzinfo=UTC),
    )


def _pause(
    shift_id: UUID,
    started_at: datetime,
    finished_at: datetime | None,
) -> PauseEntity:
    return PauseEntity(
        shift_id=shift_id,
        started_at=started_at,
        finished_at=finished_at,
    )


def test_pause_lifecycle_enforces_single_active_pause(
    time_provider: FakeTimeProvider,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )

    pause = shift.start_pause()

    assert shift.active_pause == pause
    with pytest.raises(AlreadyActiveException):
        shift.start_pause()

    time_provider.travel(datetime(2026, 9, 2, 12, 1, tzinfo=UTC))
    assert shift.finish_pause() == pause
    assert shift.active_pause is None


def test_finishing_shift_closes_active_pause_at_same_time(
    time_provider: FakeTimeProvider,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )
    pause = shift.start_pause()

    time_provider.travel(datetime(2026, 9, 2, 12, 1, tzinfo=UTC))
    shift.finish()

    expected_finished_at = datetime(2026, 9, 2, 12, 1, tzinfo=UTC)
    assert shift.finished_at == expected_finished_at
    assert pause.finished_at == expected_finished_at
    with pytest.raises(AlreadyFinishedException):
        shift.finish()
    with pytest.raises(AlreadyFinishedException):
        shift.start_pause()


def test_add_pause_accepts_adjacent_ranges() -> None:
    shift = _finished_shift()
    shift.add_pause(
        _pause(
            shift.id,
            datetime(2026, 9, 2, 10, tzinfo=UTC),
            datetime(2026, 9, 2, 11, tzinfo=UTC),
        )
    )
    before = _pause(
        shift.id,
        datetime(2026, 9, 2, 9, tzinfo=UTC),
        datetime(2026, 9, 2, 10, tzinfo=UTC),
    )
    after = _pause(
        shift.id,
        datetime(2026, 9, 2, 11, tzinfo=UTC),
        datetime(2026, 9, 2, 12, tzinfo=UTC),
    )

    assert shift.add_pause(before) == before
    assert shift.add_pause(after) == after


@pytest.mark.parametrize(
    ("started_at", "finished_at"),
    [
        ("09:30", "10:30"),
        ("10:15", "10:45"),
        ("10:00", "11:00"),
        ("09:30", "11:30"),
        ("10:30", "11:30"),
    ],
)
def test_add_pause_rejects_every_overlap_shape(
    started_at: str,
    finished_at: str,
) -> None:
    shift = _finished_shift()
    shift.add_pause(
        _pause(
            shift.id,
            datetime.fromisoformat(f"2026-09-02T{10:02d}:00+00:00"),
            datetime.fromisoformat(f"2026-09-02T{11:02d}:00+00:00"),
        )
    )

    with pytest.raises(OverlappingException):
        shift.add_pause(
            _pause(
                shift.id,
                datetime.fromisoformat(f"2026-09-02T{started_at}+00:00"),
                datetime.fromisoformat(f"2026-09-02T{finished_at}+00:00"),
            )
        )


def test_add_pause_requires_finished_shift_and_pause() -> None:
    active_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )
    finished_pause = _pause(
        active_shift.id,
        datetime(2026, 9, 2, 9, tzinfo=UTC),
        datetime(2026, 9, 2, 10, tzinfo=UTC),
    )

    with pytest.raises(UnfinishedException):
        active_shift.add_pause(finished_pause)

    finished_shift = _finished_shift()
    active_pause = _pause(
        finished_shift.id,
        datetime(2026, 9, 2, 9, tzinfo=UTC),
        None,
    )
    with pytest.raises(UnfinishedException):
        finished_shift.add_pause(active_pause)


@pytest.mark.parametrize(
    ("started_at", "finished_at"),
    [
        ("07:00", "09:00"),
        ("16:00", "18:00"),
    ],
)
def test_add_pause_rejects_ranges_outside_shift(
    started_at: str,
    finished_at: str,
) -> None:
    shift = _finished_shift()

    with pytest.raises(InvalidTimeRangeException):
        shift.add_pause(
            _pause(
                shift.id,
                datetime.fromisoformat(f"2026-09-02T{started_at}+00:00"),
                datetime.fromisoformat(f"2026-09-02T{finished_at}+00:00"),
            )
        )


def test_shift_time_range_changes_atomically_and_respects_pauses(
    time_provider: FakeTimeProvider,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 10, tzinfo=UTC),
    )

    shift.change_time_range(
        started_at=datetime(2026, 9, 2, 11, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
    )
    assert shift.started_at == datetime(2026, 9, 2, 11, tzinfo=UTC)
    assert shift.finished_at == datetime(2026, 9, 2, 12, tzinfo=UTC)

    shift.add_pause(
        _pause(
            shift.id,
            datetime(2026, 9, 2, 11, 15, tzinfo=UTC),
            datetime(2026, 9, 2, 11, 45, tzinfo=UTC),
        )
    )
    with pytest.raises(OverlappingException):
        shift.change_started_at(datetime(2026, 9, 2, 11, 30, tzinfo=UTC))
    with pytest.raises(OverlappingException):
        shift.change_finished_at(datetime(2026, 9, 2, 11, 30, tzinfo=UTC))


def test_active_shift_time_range_cannot_be_edited() -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )

    with pytest.raises(UnfinishedException):
        shift.change_started_at(datetime(2026, 9, 2, 7, tzinfo=UTC))
    with pytest.raises(UnfinishedException):
        shift.change_finished_at(datetime(2026, 9, 2, 9, tzinfo=UTC))


def test_pause_time_range_update_rejects_overlap_and_unknown_pause() -> None:
    shift = _finished_shift()
    first = _pause(
        shift.id,
        datetime(2026, 9, 2, 9, tzinfo=UTC),
        datetime(2026, 9, 2, 10, tzinfo=UTC),
    )
    second = _pause(
        shift.id,
        datetime(2026, 9, 2, 11, tzinfo=UTC),
        datetime(2026, 9, 2, 12, tzinfo=UTC),
    )
    shift.add_pause(first)
    shift.add_pause(second)

    with pytest.raises(OverlappingException):
        shift.change_pause_time_range(
            second.id,
            started_at=datetime(2026, 9, 2, 9, 30, tzinfo=UTC),
            finished_at=datetime(2026, 9, 2, 11, tzinfo=UTC),
        )
    with pytest.raises(NotFoundException):
        shift.change_pause_finished_at(
            uuid4(), datetime(2026, 9, 2, 13, tzinfo=UTC)
        )


def test_delete_pause_rejects_unknown_pause() -> None:
    with pytest.raises(NotFoundException):
        _finished_shift().delete_pause(uuid4())


def test_only_finished_shift_can_be_approved(
    time_provider: FakeTimeProvider,
) -> None:
    active_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )
    with pytest.raises(UnfinishedException):
        active_shift.approve()

    shift = _finished_shift()
    shift.approve()
    assert shift.approved
    shift.disapprove()
    assert not shift.approved


def test_total_worked_hours_excludes_finished_and_active_pauses(
    time_provider: FakeTimeProvider,
) -> None:
    finished_shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 12, tzinfo=UTC),
        pauses=[
            _pause(
                uuid4(),
                datetime(2026, 9, 2, 9, tzinfo=UTC),
                datetime(2026, 9, 2, 9, 30, tzinfo=UTC),
            )
        ],
    )
    active_shift = ShiftEntity(
        reference_id="employee-2",
        started_at=datetime(2026, 9, 2, 10, tzinfo=UTC),
        pauses=[
            _pause(
                uuid4(),
                datetime(2026, 9, 2, 11, 30, tzinfo=UTC),
                None,
            )
        ],
    )

    assert finished_shift.total_worked_hours == 3.5
    assert active_shift.total_worked_hours == 1.5


def test_start_records_shift_started_event(time_provider: FakeTimeProvider) -> None:
    shift = ShiftEntity.start(reference_id="employee-1")

    assert shift.pull_events() == (
        ShiftStartedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            started_at=NOW,
            occurrence_datetime=NOW,
        ),
    )


def test_shift_lifecycle_records_events(time_provider: FakeTimeProvider) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )

    shift.finish()
    shift.change_time_range(
        started_at=datetime(2026, 9, 2, 7, tzinfo=UTC),
        finished_at=datetime(2026, 9, 2, 13, tzinfo=UTC),
    )
    shift.approve()
    shift.approve()
    shift.disapprove()
    shift.disapprove()

    events = shift.pull_events()

    assert [type(event) for event in events] == [
        ShiftFinishedEvent,
        ShiftStartChangedEvent,
        ShiftFinishChangedEvent,
        ShiftApprovedEvent,
        ShiftRejectedEvent,
    ]
    start_changed_event = events[1]
    assert isinstance(start_changed_event, ShiftStartChangedEvent)
    assert start_changed_event.previous_started_at == datetime(
        2026, 9, 2, 8, tzinfo=UTC
    )
    finish_changed_event = events[2]
    assert isinstance(finish_changed_event, ShiftFinishChangedEvent)
    assert finish_changed_event.previous_finished_at == NOW


def test_automatically_close_records_finished_and_automatic_events(
    time_provider: FakeTimeProvider,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )

    shift.automatically_close()

    assert [type(event) for event in shift.pull_events()] == [
        ShiftFinishedEvent,
        ShiftAutomaticallyClosedEvent,
    ]


def test_events_are_isolated_and_can_be_pulled(
    time_provider: FakeTimeProvider,
) -> None:
    first = ShiftEntity.start(reference_id="employee-1")
    second = ShiftEntity(reference_id="employee-2")

    assert second.pull_events() == ()
    assert len(first.pull_events()) == 1
    assert first.pull_events() == ()


def test_delete_records_shift_deleted_event(
    time_provider: FakeTimeProvider,
) -> None:
    shift = _finished_shift()

    shift.delete()

    assert shift.pull_events() == (
        ShiftDeletedEvent(
            reference_id=shift.reference_id,
            shift_id=shift.id,
            occurrence_datetime=NOW,
        ),
    )
