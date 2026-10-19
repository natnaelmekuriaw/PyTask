# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE} AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY constraints/runtime.txt constraints/runtime.txt
COPY src/ src/
RUN python -m pip wheel --only-binary=:all: --wheel-dir /wheels \
    --constraint constraints/runtime.txt . \
    && python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-index \
    --find-links=/wheels pytask-service

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTASK_ALEMBIC_CONFIG=/app/alembic.ini
WORKDIR /app
RUN groupadd --gid 10001 pytask \
    && useradd --uid 10001 --gid 10001 --no-create-home \
    --shell /usr/sbin/nologin pytask
COPY --from=build /opt/venv /opt/venv
COPY alembic.ini LICENSE ./
COPY migrations/ migrations/
USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM
ENTRYPOINT ["/opt/venv/bin/python", "-m", "pytask_service.runtime"]
CMD ["api"]
