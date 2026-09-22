from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domains.shifts.routes import shift_router
from src.domains.pauses.routes import pause_router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(shift_router)
    app.include_router(pause_router)
    return TestClient(app)


def test_clock_route_returns_shift_id(client: TestClient) -> None:
    response = client.post("/shift/clock", params={"reference_id": "employee-1"})

    assert response.status_code == 200, response.text
    assert UUID(response.json())


@pytest.mark.parametrize("path", ["/shift/clock", "/pause/clock"])
def test_clock_rejects_oversized_reference_id(client: TestClient, path: str) -> None:
    response = client.post(path, params={"reference_id": "x" * 256})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_long"


def test_clock_accepts_255_character_reference_id(client: TestClient) -> None:
    response = client.post("/shift/clock", params={"reference_id": "x" * 255})
    assert response.status_code == 200, response.text


def test_save_rejects_oversized_reference_id(client: TestClient) -> None:
    response = client.post(
        "/shift/save", json={"id": str(uuid4()), "reference_id": "x" * 256}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_long"


def test_reference_route_translates_filters_and_pagination(
    client: TestClient,
) -> None:
    response = client.get(
        "/shift/reference/employee-1",
        params={
            "approved": "false",
            "automatically_closed": "true",
            "is_open": "false",
            "sort_direction": "asc",
            "limit": 20,
            "offset": 5,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 5,
    }
