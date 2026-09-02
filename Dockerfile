FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

FROM builder AS dev-envs

RUN useradd --create-home --shell /bin/bash vscode \
    && groupadd docker \
    && usermod -aG docker vscode

# Install Docker CLI, Buildx and Compose
COPY --from=gloursdocker/docker / /

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
