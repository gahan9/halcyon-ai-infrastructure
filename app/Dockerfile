# SPDX-License-Identifier: MIT
# Stage 1: install dependencies with uv into an isolated venv.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /build
RUN pip install --no-cache-dir uv==0.6.14

COPY pyproject.toml README.md ./
COPY src ./src
RUN uv sync --no-dev --no-editable

# Stage 2: copy only the runtime venv into a minimal non-root image.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    APP_PORT=8080

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build/src /app/src
ENV PYTHONPATH=/app/src

USER appuser
EXPOSE 8080
# Default to API; App Spec overrides worker command.
CMD ["python", "-m", "halcyon_sim.api"]
