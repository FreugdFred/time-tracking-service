# Time Tracking Service API

The Time Tracking Service records work shifts and pauses for an external
reference such as an employee, contractor, device, or account ID.

Use the HTTP API to:

- clock a shift in or out;
- start or finish a pause in the active shift;
- create or correct historical shifts and pauses;
- approve completed shifts;
- query shifts and pauses; and
- receive lifecycle events through NATS.

The examples below use `http://localhost:8000` as the base URL and
`employee-123` as the consumer-owned reference ID.

## Contents

- [Start the service](#start-the-service)
- [Authentication](#authentication)
- [Data conventions](#data-conventions)
- [Common workflow](#common-workflow)
- [Shift API](#shift-api)
- [Pause API](#pause-api)
- [HTTP errors](#http-errors)
- [NATS events](#nats-events)
- [Configuration](#configuration)

## Start the service

### Docker Compose

In the workspace distribution, `compose.yml` is located next to the
`time-tracking-service` directory. From that parent directory, run:

```console
docker compose up --build
```

This starts:

- the API at <http://localhost:8000>;
- PostgreSQL for persistent storage;
- NATS at `nats://localhost:4222`; and
- the NATS monitoring endpoint at <http://localhost:8222>.

The API container applies Alembic migrations before starting.

Useful endpoints:

- Interactive API documentation: <http://localhost:8000/docs>
- OpenAPI document: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

### Run directly

Python 3.13+, Git, uv, PostgreSQL, and optionally NATS are required.

```console
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Set at least `DATABASE_URL` in the process environment before running these
commands. For example:

```text
DATABASE_URL=postgresql+asyncpg://time_tracking:time_tracking@localhost:5432/time_tracking
NATS_URL=nats://localhost:4222
```

## Authentication

Authentication is disabled when `API_KEY` is unset. When it is configured,
send the key in every shift and pause request:

```http
X-API-Key: your-api-key
```

For example:

```console
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/shift/reference/employee-123"
```

The health endpoint remains available without an API key.

## Data conventions

### Reference IDs

`reference_id` is an opaque string controlled by the API consumer. It is
commonly an employee ID, but the service does not interpret or validate its
format.

Swagger UI uses `"string"` as a generated placeholder. If that value is sent,
the service stores the literal value `string`. Replace generated examples with
your real reference ID or omit the field when it is not part of an update.

### Timestamps

Send ISO 8601 timestamps with a UTC marker or explicit offset:

```text
2026-09-03T08:00:00Z
2026-09-03T10:00:00+02:00
```

Timestamps are normalized to UTC for persistence and responses. The service
currently accepts future time ranges when all other validation rules pass.

Time ranges behave as half-open intervals: `[started_at, finished_at)`.
Adjacent shifts or pauses are allowed; ranges that share actual time are not.

### Shift and pause lifecycle

- One reference can have at most one active shift.
- One shift can have at most one active pause.
- Clocking a shift with no active shift starts one.
- Clocking a shift with an active shift finishes it.
- Finishing a shift also finishes its active pause at the same time.
- Clocking a pause requires an active shift.
- Clocking a pause starts one when none is active and finishes the active pause
  otherwise.
- Manual pauses must be contained by their shift and cannot overlap another
  pause in that shift.
- Deleting a shift also deletes its pauses.
- Delete operations are idempotent; deleting a missing ID succeeds as a no-op.

## Common workflow

### 1. Clock in

```console
curl -X POST \
  "http://localhost:8000/shift/clock?reference_id=employee-123"
```

Response:

```json
"018f6f1e-7f89-7f44-a5b9-c62a854d24d8"
```

Keep this UUID if you later need to retrieve, correct, approve, or remove the
shift.

### 2. Start a pause

```console
curl -X POST \
  "http://localhost:8000/pause/clock?reference_id=employee-123"
```

Response:

```json
"018f6f34-f156-75aa-b531-94192d03cb49"
```

### 3. Finish the pause

Call the same endpoint again:

```console
curl -X POST \
  "http://localhost:8000/pause/clock?reference_id=employee-123"
```

The response contains the same pause UUID.

If no active shift exists, the API returns:

```json
{
  "detail": "Cannot clock a pause because no active shift was found for reference 'employee-123'. Start a shift first."
}
```

### 4. Clock out

```console
curl -X POST \
  "http://localhost:8000/shift/clock?reference_id=employee-123"
```

The response contains the UUID of the shift that was finished.

## Shift API

### Clock a shift

`POST /shift/clock?reference_id={reference_id}`

Starts or finishes the active shift for the reference. Returns the affected
shift UUID as a JSON string.

### Save a shift

`POST /shift/save`

This endpoint is an upsert:

- when `id` does not exist, it creates a completed historical shift;
- when `id` exists, it updates that shift.

On updates, `automatically_closed` and `approved` currently default to `false`
when omitted. Include their intended values in every save request if either
flag may already be `true`.

Creating a shift requires `id`, `reference_id`, `started_at`, and
`finished_at`:

```console
curl -X POST "http://localhost:8000/shift/save" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
    "reference_id": "employee-123",
    "started_at": "2026-09-03T08:00:00Z",
    "finished_at": "2026-09-03T16:30:00Z",
    "automatically_closed": false,
    "approved": false
  }'
```

To correct a finish time, send the shift ID and the field being changed. Do
not copy Swagger placeholders into the request:

```console
curl -X POST "http://localhost:8000/shift/save" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
    "finished_at": "2026-09-03T17:00:00Z",
    "automatically_closed": false,
    "approved": false
  }'
```

The response is `null`. A shift update is rejected when its final time range
overlaps another shift for the same reference or no longer contains all of its
pauses.

### Remove a shift

`DELETE /shift/remove?id={shift_id}`

```console
curl -X DELETE \
  "http://localhost:8000/shift/remove?id=018f6f1e-7f89-7f44-a5b9-c62a854d24d8"
```

The response is `null`. Removing an unknown ID is also successful.

### Get a shift

`GET /shift/{shift_id}`

```console
curl \
  "http://localhost:8000/shift/018f6f1e-7f89-7f44-a5b9-c62a854d24d8"
```

Response:

```json
{
  "started_at": "2026-09-03T08:00:00Z",
  "finished_at": "2026-09-03T16:30:00Z",
  "pauses": [
    {
      "started_at": "2026-09-03T12:00:00Z",
      "finished_at": "2026-09-03T12:30:00Z"
    }
  ],
  "automatically_closed": false,
  "approved": false,
  "reference_id": "employee-123"
}
```

The current shift projection does not repeat the shift UUID in its response;
the UUID is supplied in the request path.

### List shifts for a reference

`GET /shift/reference/{reference_id}`

Available query parameters:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `approved` | unset | Filter by approval state. |
| `automatically_closed` | unset | Filter shifts closed by the scheduler. |
| `is_open` | unset | `true` for active shifts; `false` for finished shifts. |
| `sort_direction` | `desc` | Sort by start time using `asc` or `desc`. |
| `limit` | `10` | Page size from 0 through 100. |
| `offset` | `0` | Number of matching rows to skip. |

```console
curl \
  "http://localhost:8000/shift/reference/employee-123?is_open=false&sort_direction=desc&limit=10&offset=0"
```

Response:

```json
{
  "items": [
    {
      "started_at": "2026-09-03T08:00:00Z",
      "finished_at": "2026-09-03T16:30:00Z",
      "pauses": [],
      "automatically_closed": false,
      "approved": false
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

`total` is the number of all matching shifts before pagination.

### List shifts in a date range

`GET /shift/date-range`

Required query parameters are `start` and `end`. The endpoint returns shifts
that overlap the requested window. It supports the same filters and pagination
parameters as the reference endpoint, plus an optional `reference_id`.

```console
curl \
  "http://localhost:8000/shift/date-range?start=2026-09-01T00%3A00%3A00Z&end=2026-09-08T00%3A00%3A00Z&reference_id=employee-123&limit=25&offset=0"
```

The paginated response uses the same shape as the reference query, with
`reference_id` included in every item.

## Pause API

### Clock a pause

`POST /pause/clock?reference_id={reference_id}`

Starts or finishes the active pause in the reference's active shift. Returns
the affected pause UUID as a JSON string.

### Save a pause

`POST /pause/save`

This endpoint is an upsert. Creating a historical pause requires `id`,
`shift_id`, `started_at`, and `finished_at`. The target shift must already be
finished.

```console
curl -X POST "http://localhost:8000/pause/save" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "018f6f34-f156-75aa-b531-94192d03cb49",
    "shift_id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
    "started_at": "2026-09-03T12:00:00Z",
    "finished_at": "2026-09-03T12:30:00Z"
  }'
```

For an existing pause, send its ID and the time fields to correct. A pause
cannot be moved to another shift. The final pause range must remain inside its
shift and must not overlap another pause.

The response is `null`.

### Remove a pause

`DELETE /pause/remove?id={pause_id}`

```console
curl -X DELETE \
  "http://localhost:8000/pause/remove?id=018f6f34-f156-75aa-b531-94192d03cb49"
```

The response is `null`. Removing an unknown ID is also successful.

### Get a pause

`GET /pause/{pause_id}`

Response:

```json
{
  "id": "018f6f34-f156-75aa-b531-94192d03cb49",
  "shift_id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
  "started_at": "2026-09-03T12:00:00Z",
  "finished_at": "2026-09-03T12:30:00Z"
}
```

## HTTP errors

Error responses use this shape:

```json
{
  "detail": "Human-readable explanation"
}
```

| Status | Meaning |
| --- | --- |
| `401 Unauthorized` | The API key is missing or invalid when authentication is enabled. |
| `404 Not Found` | A requested resource, or the active shift required by pause clocking, does not exist. |
| `409 Conflict` | The requested lifecycle transition is invalid or a time range overlaps existing data. |
| `422 Unprocessable Content` | The body is incomplete or contains an invalid time range. |

Pydantic request-parsing errors also return HTTP 422 with FastAPI's standard
validation-error structure.

## NATS events

When `NATS_URL` is configured, successful command handlers publish domain
events after persistence. When it is unset, commands still work but publish no
events.

Subjects use this format:

```text
{PROJECT_NAME}.{EventClassName}
```

With the default project name, examples include:

```text
Time-Tracking-Service-API.ShiftStartedEvent
Time-Tracking-Service-API.PauseFinishedEvent
```

Subscribe to every event from this service with:

```text
Time-Tracking-Service-API.*
```

Available event classes:

- `ShiftStartedEvent`
- `ShiftFinishedEvent`
- `ShiftStartChangedEvent`
- `ShiftFinishChangedEvent`
- `ShiftApprovedEvent`
- `ShiftRejectedEvent`
- `ShiftAutomaticallyClosedEvent`
- `ShiftDeletedEvent`
- `PauseStartedEvent`
- `PauseFinishedEvent`
- `PauseStartChangedEvent`
- `PauseFinishChangedEvent`
- `PauseDeletedEvent`

Every payload contains `reference_id` and `occurrence_datetime`. Shift events
also contain `shift_id`; pause events contain both `shift_id` and `pause_id`.
Change events include the previous and new effective value:

```json
{
  "reference_id": "employee-123",
  "occurrence_datetime": "2026-09-03T09:15:00Z",
  "shift_id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
  "previous_finished_at": "2026-09-03T16:30:00Z",
  "finished_at": "2026-09-03T17:00:00Z"
}
```

`occurrence_datetime` is when the change occurred. `started_at`, `finished_at`,
and `previous_*` fields are effective business timestamps, so they may be
earlier or later than the event occurrence time.

Events are currently published through Core NATS. The service does not create
a JetStream stream or durable consumer; consumers that require persistence or
replay must configure that infrastructure separately.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | none | SQLAlchemy async database URL, normally using `postgresql+asyncpg`. |
| `NATS_URL` | No | none | NATS connection URL. Event publication is disabled when unset. |
| `API_KEY` | No | none | Enables `X-API-Key` authentication for shift and pause routes. |
| `PROJECT_NAME` | No | `Time-Tracking-Service-API` | API title and NATS subject prefix. |
| `LOCAL_TIMEZONE` | No | `Europe/Amsterdam` | Local timezone used by the service clock. |
| `SHIFT_AUTO_CLOSE_AFTER_HOURS` | No | `12` | Age after which the scheduler closes active shifts. |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `DEBUG` | No | `false` | Enables FastAPI debug mode. |

The automatic-close scheduler runs once per minute. When it closes a shift, it
also closes any active pause and publishes the corresponding lifecycle events
when NATS is enabled.
