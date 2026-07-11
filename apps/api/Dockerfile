FROM python:3.12-alpine AS builder

RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev cargo

RUN pip install uv --no-cache-dir

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-cache

FROM python:3.12-alpine AS runner

RUN apk add --no-cache libffi postgresql-client wget curl

RUN addgroup -S astra && adduser -S astra -G astra

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY alembic.ini alembic/ entrypoint.sh ./
COPY app/ ./app/

RUN chmod +x /app/entrypoint.sh && chown -R astra:astra /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/v1/health || \
        curl -sf http://localhost:8000/api/v1/health || exit 1

USER astra

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"

CMD ["/app/entrypoint.sh"]
