# Time Tracking Service: Architecture and Working Guide

This service is a FastAPI application built with SQLAlchemy, Pydantic, and a
small dependency-injection container. The code is organized by business
domain and follows CQRS: writes are commands, reads are queries.

## How a request flows

Write requests follow this path:

`route -> command -> command handler -> domain entity -> command repository`

Read requests follow this path:

`route -> query -> query handler -> query repository -> query model`

Keep these paths separate. A query must not mutate state, and a command should
not return a read projection when an identifier or no response is sufficient.

## Domain layout

Each domain lives under `src/domains/<domain>/`. Use this layout when adding a
feature:

```text
<domain>/
  commands/
    <use_case>/
      command.py
      handler.py
  queries/
    <use_case>/
      query.py
      handler.py
  entity.py
  models.py
  mapper.py
  schemas.py
  query_models.py
  command_repository.py   # when the domain owns persisted writes
  query_repository.py
  routes.py
  di.py
```

Not every domain needs every file. Do not add abstractions until there is a
real use for them.

## CQRS conventions

- Commands describe an intent to change state. Name them with an imperative
  use case, such as `SavePauseCommand` or `ClockShiftCommand`.
- Command handlers orchestrate one use case. They load an aggregate, call
  domain methods, and persist the result.
- Queries describe requested data. Name them after the read operation, such as
  `GetPauseByIdQuery`.
- Query handlers delegate reads to a query repository and translate missing
  results into domain exceptions.
- Query repositories return query models, not domain entities or SQLAlchemy
  models.
- Routes only translate HTTP input into a command or query and resolve the
  matching handler. Business rules do not belong in routes.

## Aggregate ownership

`ShiftEntity` is the aggregate root. A pause belongs to a shift and its valid
time range depends on that shift and its other pauses.

For that reason:

- Pause commands load and save `ShiftEntity` through
  `CommandShiftRepository`.
- Pause commands use methods such as `start_pause`, `finish_pause`,
  `add_pause`, `delete_pause`, and `change_pause_time_range`.
- Do not update or delete `DbPause` directly from a command handler. Doing so
  would bypass shift-boundary and overlap rules.
- Pause queries may read `DbPause` directly through `QueryPauseRepository`
  because reads do not change aggregate state.

## Where validation belongs

Use the narrowest layer that has enough information to enforce a rule:

- Schemas and command/query models validate input shape and simple field
  relationships.
- Domain entities enforce business invariants, including lifecycle rules,
  valid time ranges, and overlap rules inside an aggregate.
- Command handlers coordinate validations that require loading data.
- Repositories own SQL and persistence concerns. Expose cross-record checks as
  explicit methods so handlers can fail early. Recheck critical invariants in
  the write repository immediately before persistence as a final guard.
- Database constraints are the final protection for invariants that must hold
  under concurrent requests.

Time ranges use half-open interval behavior: `[started_at, finished_at)`.
Adjacent ranges are valid; ranges with actual shared time overlap.

## Persistence rules

- Keep SQLAlchemy models inside `models.py` and domain behavior inside
  `entity.py`.
- Use mappers when moving between database models and domain entities.
- Eager-load relationships needed by the aggregate before leaving a session.
- Keep sessions short-lived and commit only after domain validation succeeds.
- Exclude the current record when checking overlap during an update.
- `CommandShiftRepository.save` must recheck shift overlap using the same
  session as the write. Do not remove the earlier handler check; it provides a
  clearer early failure while the repository protects every save path.
- Treat `None` as an open-ended finish only where the domain supports an
  active shift or pause.
- Prefer one transaction for a read-modify-write operation when concurrency
  can affect correctness.

## API and error behavior

- Use Pydantic schemas for request bodies and query models for responses.
- Return UUIDs from clock operations so the caller can identify the affected
  resource.
- Delete operations are idempotent: deleting a missing shift or pause is a
  successful no-op.
- Raise domain exceptions from entities and handlers. Map them to HTTP status
  codes centrally in `src/exception_handlers.py`.
- Use `NotFoundException` for missing resources, `ValidationException` for an
  invalid operation or incomplete create request, and
  `OverlappingException` for conflicting time ranges.

## Dependency injection

Every repository and handler used by a route must be registered in the
domain's `di.py`. Each domain registration function must then be called from
`src/dependencies.py`.

When adding a route, verify all of the following:

1. The route resolves a handler, not a repository.
2. The handler and its repository are registered.
3. The command or query name matches its CQRS side.
4. The response model exposes only the intended API fields.

## Coding practices

- Use timezone-aware datetimes. Domain code obtains the current time through
  `AbstractTimeProvider`; do not call `datetime.now()` directly in entities or
  handlers.
- Use explicit `is None` and `is not None` checks for optional values. Do not
  use truthiness when zero, `False`, or an empty value has meaning.
- For partial updates, distinguish omitted fields from explicitly supplied
  values with Pydantic's `model_fields_set` where necessary.
- Validate and apply a complete time-range change atomically. Do not mutate the
  start and finish separately when an intermediate range could be invalid.
- Keep handlers small. Move reusable business decisions into entities and SQL
  construction into repositories.
- Never use Python dataclasses. Use Pydantic models for structured data,
  SQLAlchemy models for persistence, or regular classes for behavior.
- Preserve existing user changes in a dirty working tree and keep unrelated
  refactors out of feature work.

## Tests and checks

Add tests at the same time as business behavior. Do not add tests merely to
cover infrastructure, logging, dependency wiring, or other mechanical changes;
verify those changes with the existing checks unless they implement a business
rule.

Use pytest functions and fixtures; do not write class-based tests. Test
business behavior through entity tests and handlers resolved from `Dependency`
with the real repositories. Add a small number of route tests for HTTP parsing,
response shape, and handler dispatch without repeating handler scenarios.
Assert the observable result, state change, or domain error. Do not add
repository, SQL-construction, dependency-wiring, logging, or other
infrastructure tests merely for coverage. Mirror the source domain structure
under `tests/`.

Do not use `unittest.mock`, `Mock`, `AsyncMock`, or patch dependency lookups in
tests. Do not create fake repositories or fake handlers. Register or override
test dependencies through `Dependency`, and resolve handlers and repositories
from the container so tests follow production dependency wiring.

Use the shared `FakeTimeProvider` fixture from `tests/conftest.py`. Move time
with `travel()`, `forward()`, or `backward()` when a scenario needs a different
instant; do not define per-module clock mocks or duplicate clock fixtures.

Tests that need persistence may create an isolated SQLite database. Register
its session manager through `Dependency` and use the real repositories; do not
require PostgreSQL or another external database service for the test suite.

Before handing off a change, run:

```text
uv run ruff check src tests
uv run pyright src tests
uv run pytest
```

The application settings require `DATABASE_URL` and `NATS_URL`. Supply local
test values through the environment or an uncommitted `.env` file; never put
credentials in source code or tests.
