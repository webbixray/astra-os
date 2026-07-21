# ============================================================
# ASTRA OS API - Production Dockerfile
# Multi-stage build with minimal attack surface
# Deterministic builds via uv sync --frozen
# ============================================================

# Stage 1: Builder - Install dependencies
FROM ghcr.io/astral-sh/uv:latest AS uv
FROM python:3.14-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for deterministic dependency resolution
COPY --from=uv /uv /bin/uv
RUN chmod +x /bin/uv

WORKDIR /build

# Copy dependency manifests first for layer caching
COPY apps/api/pyproject.toml apps/api/uv.lock ./
COPY services/agent_orchestrator/pyproject.toml services/agent_orchestrator/uv.lock ./services/agent_orchestrator/
RUN uv sync --frozen --no-dev
# Install local packages into the same virtual environment
RUN uv pip install --python /build/.venv/bin/python --no-deps -e ./services/agent_orchestrator

# Stage 2: Runtime
FROM python:3.14-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r astra && useradd -r -g astra -d /app -s /sbin/nologin astra

# Copy virtual environment from builder
COPY --from=builder /build/.venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application code
COPY --chown=astra:astra apps/api/app ./app
COPY --chown=astra:astra apps/api/alembic ./alembic
COPY --chown=astra:astra apps/api/alembic.ini ./alembic.ini
COPY --chown=astra:astra apps/api/entrypoint.py ./entrypoint.py
COPY --chown=astra:astra services/agent_orchestrator ./services/agent_orchestrator

# Create required directories
RUN mkdir -p /app/config /app/logs && chown -R astra:astra /app

# Switch to non-root user
USER astra

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
