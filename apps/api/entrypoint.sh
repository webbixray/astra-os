#!/bin/sh
set -e
.venv/bin/python -m alembic upgrade head
exec .venv/bin/gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --max-requests 10000 --max-requests-jitter 1000
