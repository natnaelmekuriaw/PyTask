ARG PYTASK_BASE=pytask:local
FROM ${PYTASK_BASE}
COPY --chown=0:0 handlers.py /opt/tasks/handlers.py
ENV PYTHONPATH=/opt/tasks \
    PYTASK_REGISTRY=handlers:registry
