# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.12.5 AS uv

FROM python:3.12-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system tihbc \
    && useradd --system --gid tihbc --home-dir /app --shell /usr/sbin/nologin tihbc \
    && mkdir --parents /app /data/media \
    && chown --recursive tihbc:tihbc /app /data/media

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=tihbc:tihbc alembic ./alembic
COPY --chown=tihbc:tihbc alembic.ini pyproject.toml ./
COPY --chown=tihbc:tihbc app ./app
COPY --chown=tihbc:tihbc docker-entrypoint.sh ./docker-entrypoint.sh
RUN sed -i 's/\r$//' ./docker-entrypoint.sh && chmod 755 ./docker-entrypoint.sh

USER tihbc

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
