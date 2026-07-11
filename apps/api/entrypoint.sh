#!/bin/sh
set -e

echo "Running database migrations..."
uv run python -m alembic upgrade head

echo "Seeding database..."
uv run python -m scripts.seed_db || true

echo "Starting API server..."
exec uv run gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --max-requests 10000 --max-requests-jitter 1000
