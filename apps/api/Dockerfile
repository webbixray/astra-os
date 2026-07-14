# ============================================================
# ASTRA API - Hardened Multi-Stage Dockerfile
# Security: distroless runtime, non-root, read-only, signed
# ============================================================

# Stage 1: Builder with all build tools
FROM python:3.12-slim AS builder

# Install build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install production dependencies only
RUN uv pip install --no-cache-dir -r pyproject.toml

# ============================================================
# Stage 2: Runtime - Distroless for minimal attack surface
# ============================================================
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code (as nonroot user)
COPY --from=builder --chown=nonroot:nonroot /app /app
COPY --chown=nonroot:nonroot alembic.ini alembic/ ./
COPY --chown=nonroot:nonroot app/ ./app/
COPY --chown=nonroot:nonroot entrypoint.py ./

# Use non-root user (distroless provides 'nonroot' UID 65532)
USER nonroot

# Expose port
EXPOSE 8000

# Default command - runs as nonroot
CMD ["python", "entrypoint.py"]

# ============================================================
# Build metadata labels (for SBOM and provenance)
# ============================================================
LABEL org.opencontainers.image.title="Astra API" \
      org.opencontainers.image.description="AI-Native Marketing & Business Growth Operating System API" \
      org.opencontainers.image.vendor="Astra OS" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/astra-os/astra-os" \
      org.opencontainers.image.documentation="https://docs.astra-os.io" \
      org.opencontainers.image.base.name="astra.build-dateastra.os.versionastra.vcs-ref