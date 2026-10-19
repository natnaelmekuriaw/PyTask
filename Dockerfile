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
