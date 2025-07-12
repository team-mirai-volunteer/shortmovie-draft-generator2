# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
COPY uv.lock* .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

COPY --chown=appuser:appuser . .

USER appuser
