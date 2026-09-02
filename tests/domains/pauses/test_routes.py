from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domains.shifts.command_repository import CommandShiftRepository
from src.domains.shifts.entity import ShiftEntity
from src.domains.pauses.routes import pause_router
from src.exception_handlers import register_exception_handlers


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(pause_router)
    register_exception_handlers(app)
    return TestClient(app)


async def test_clock_route_returns_started_pause_id(
    client: TestClient,
    command_shift_repository: CommandShiftRepository,
) -> None:
    shift = ShiftEntity(
        reference_id="employee-1",
        started_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )
    await command_shift_repository.save(shift)

    response = client.post("/pause/clock", params={"reference_id": "employee-1"})

    assert response.status_code == 200
    pause_id = UUID(response.json())
    saved_shift = await command_shift_repository.get(shift.id)
    assert saved_shift is not None
    assert saved_shift.get_pause(pause_id).shift_id == shift.id


def test_clock_route_explains_that_an_active_shift_is_required(
    client: TestClient,
) -> None:
    response = client.post("/pause/clock", params={"reference_id": "aa"})

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Cannot clock a pause because no active shift was found for reference "
            "'aa'. Start a shift first."
        )
    }
