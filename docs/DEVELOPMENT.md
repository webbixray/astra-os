# ASTRA OS - Developer Quick Start

## Prerequisites
- Python 3.12+
- Node.js 20+
- pnpm 9+
- Docker (for database and Redis)
- PostgreSQL 16
- Redis 7

## Setup

### 1. Install dependencies

```bash
# Backend
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd apps/web
pnpm install --frozen-lockfile
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis
```

### 3. Run database migrations

```bash
cd apps/api
alembic upgrade head
```

### 4. Start development servers

```bash
# Backend (port 8000)
cd apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (port 3000)
cd apps/web
pnpm dev
```

## Testing

### Backend

```bash
cd apps/api
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v --tb=short

# Run specific test file
python -m pytest tests/unit/test_encryption.py -v

# Run with coverage
python -m pytest tests/unit/ -v --cov=app --cov-report=term
```

### Frontend

```bash
cd apps/web

# Run unit tests
pnpm test

# Run end-to-end tests
pnpm test:e2e
```

## Linting & Formatting

### Backend

```bash
cd apps/api
source .venv/bin/activate

# Format code
ruff format .

# Run linter
ruff check .

# Type checking
mypy .
```

### Frontend

```bash
cd apps/web

# Lint
pnpm lint

# Type check
pnpm typecheck
```

## Database Management

### Create a new migration

```bash
cd apps/api
source .venv/bin/activate
alembic revision --autogenerate -m "description_of_change"
```

### Verify migration tree is linear

```bash
./scripts/check-migrations.sh
```

### Backup database

```bash
./scripts/db-backup.sh
```

## Deployment

### Production (Gunicorn + Uvicorn)

```bash
cd apps/api
alembic upgrade head
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --max-requests 10000 --max-requests-jitter 1000
```

### Docker deployment

```bash
docker build -f Dockerfile.prod -t astra-os-api .
docker run -d -p 8000:8000 astra-os-api
```

## Release Process

1. Ensure all tests pass: `python -m pytest tests/ -v`
2. Run full lint suite: `ruff format . --check && ruff check . && mypy .`
3. Run frontend checks: `pnpm lint && pnpm typecheck && pnpm test`
4. Tag the release: `git tag -a v1.0.0 -m "Release v1.0.0"`
5. Push tags: `git push --tags`
6. Update changelog
7. Deploy to staging and run smoke tests
8. Deploy to production