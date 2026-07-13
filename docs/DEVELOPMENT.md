# ASTRA OS — Development Guide

**Version**: 1.0  
**Purpose**: Complete guide for developing, testing, and contributing to ASTRA OS

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Backend Development](#backend-development)
6. [Frontend Development](#frontend-development)
7. [Testing](#testing)
8. [Database](#database)
9. [Debugging](#debugging)
10. [Code Quality](#code-quality)
11. [CI/CD](#cicd)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Tool | Version | Install Command |
|------|---------|-----------------|
| **Python** | 3.12+ | `brew install python@3.12` / `apt install python3.12` |
| **Node.js** | 20+ | `brew install node@20` / `nvm install 20` |
| **pnpm** | 9+ | `npm install -g pnpm` |
| **PostgreSQL** | 16 | `brew install postgresql@16` / `apt install postgresql-16` |
| **Redis** | 7+ | `brew install redis` / `apt install redis-server` |
| **Docker** | 24+ | `brew install docker` / Docker Desktop |
| **kubectl** | 1.28+ | `brew install kubectl` |
| **git** | 2.40+ | `brew install git` |

### Recommended VS Code Extensions

- Python (Microsoft)
- Pylance
- TypeScript/TypeScript Hero
- Tailwind CSS IntelliSense
- Docker
- GitLens
- Thunder Client (API testing)
- GitHub Actions

---

## Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone https://github.com/webbixray/astra-os.git
cd astra-os

# Install Python dependencies
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install frontend dependencies
cd ../web
pnpm install

# Return to root
cd ../..
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL & Redis
docker-compose up -d postgres redis

# Or use local installations
brew services start postgresql@16
brew services start redis
```

### 3. Run Migrations

```bash
cd apps/api
alembic upgrade head
```

### 4. Seed Development Data

```bash
python scripts/seed_db.py
```

### 5. Start Development Servers

**Terminal 1 - Backend:**
```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd apps/web
pnpm dev
```

**Terminal 3 - Celery Workers (optional):**
```bash
cd apps/api
celery -A app.infrastructure.celery worker -l info
```

### 6. Verify

- **API**: http://localhost:8000/api/v1/docs
- **Frontend**: http://localhost:3000
- **Health**: http://localhost:8000/api/v1/health

---

## Project Structure

```
astra-os/
├── apps/
│   ├── api/                    # FastAPI Backend
│   │   ├── app/
│   │   │   ├── domain/         # Domain Layer (Pure Python)
│   │   │   │   ├── entities/   # Entities, Value Objects, Aggregates
│   │   │   │   ├── events/     # Domain Events
│   │   │   │   ├── exceptions/ # Domain Exceptions
│   │   │   │   ├── services/   # Domain Services
│   │   │   │   └── policies/   # Domain Policies
│   │   │   ├── application/    # Application Layer
│   │   │   │   ├── use_cases/  # Use Cases
│   │   │   │   └── dtos/       # Data Transfer Objects
│   │   │   ├── infrastructure/ # Infrastructure Layer
│   │   │   │   ├── db/         # SQLAlchemy Models, Repositories
│   │   │   │   ├── cache/      # Redis Cache
│   │   │   │   ├── external_adapters/ # External API Adapters
│   │   │   │   ├── celery/     # Celery Workers
│   │   │   │   └── startup/    # Startup Probes
│   │   │   └── presentation/   # Presentation Layer
│   │   │       ├── routes/     # FastAPI Routes
│   │   │       ├── middleware/ # Middleware
│   │   │       ├── dependencies/ # FastAPI Dependencies
│   │   │       ├── schemas/    # Pydantic Schemas
│   │   │       └── error_handlers.py
│   │   ├── scripts/            # Utility Scripts
│   │   └── tests/              # Backend Tests
│   │       ├── unit/           # Unit Tests
│   │       ├── integration/    # Integration Tests
│   │       └── conftest.py     # Pytest Fixtures
│   │
│   └── web/                    # Next.js Frontend
│       ├── src/
│       │   ├── app/            # App Router Pages
│       │   ├── features/       # Feature Modules
│       │   ├── components/     # Shared Components
│       │   ├── lib/            # Utilities, API Client
│       │   └── hooks/          # Custom Hooks
│       └── tests/              # Frontend Tests
│
├── services/                   # Shared Microservices
│   └── agent_orchestrator/     # Agent Orchestration Service
│
├── packages/                   # Shared Packages (pnpm workspace)
│   ├── ui/                     # Shared UI Components
│   ├── config/                 # Shared Config (ESLint, TS, Tailwind)
│   └── types/                  # Shared TypeScript Types
│
├── docker/                     # Dockerfiles
├── k8s/                        # Kubernetes Manifests (Kustomize)
├── scripts/                    # Utility Scripts
└── docs/                       # Documentation
```

---

## Development Workflow

### 1. Feature Branch

```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Make changes
# ... code changes ...

# Run tests locally
make test

# Commit with conventional commits
git add .
git commit -m "feat: add shadow mode lift calculation"
```

### 2. Pull Request

```bash
# Push branch
git push origin feat/your-feature-name

# Create PR on GitHub
# - Fill PR template
# - Link related issues
# - Request review
```

### 3. Code Review Checklist

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Types check (`make typecheck`)
- [ ] No security issues
- [ ] Documentation updated
- [ ] Changelog entry added (CHANGELOG.md) updated

### 4. Merge

```bash
# Squash and merge on GitHub
# Delete branch after merge
```

---

## Backend Development

### Adding a New Domain Entity

```python
# apps/api/app/domain/entities/your_domain/your_entity.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class YourEntity:
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    name: str = ""
    created_at: datetime = field(default_factory=now)
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }
```

### Adding a Domain Service

```python
# apps/api/app/domain/services/your_service.py
from __future__ import annotations
from typing import Any
from uuid import UUID

class YourService:
    def __init__(self, repo: YourRepository):
        self.repo = repo
    
    async def do_something(self, org_id: UUID, data: dict) -> Any:
        # Business logic here
        pass
```

### Adding a Repository

```python
# apps/api/app/infrastructure/db/repositories/your_repo.py
from __future__ import annotations
from typing import Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

class YourRepositoryImpl:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def save(self, entity: YourEntity) -> YourEntity:
        # Save logic
        pass
```

### Adding a Use Case

```python
# apps/api/app/application/use_cases/your_use_case.py
from __future__ import annotations
from uuid import UUID

class YourUseCase:
    def __init__(self, repo: YourRepository):
        self.repo = repo
    
    async def execute(self, org_id: UUID, data: dict) -> Any:
        # Orchestration logic
        pass
```

### Adding API Routes

```python
# apps/api/app/presentation/routes/your_routes.py
from fastapi import APIRouter, Depends, Query
from uuid import UUID

router = APIRouter(prefix="/your-feature", tags=["your-feature"])

@router.post("", status_code=201)
async def create_feature(
    request: CreateRequest,
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Implementation
    pass
```

### Register Routes

```python
# apps/api/app/main.py
from app.presentation.routes import your_routes
app.include_router(your_routes.router, prefix="/api/v1")
```

---

## Frontend Development

### Adding a New Feature Page

```
apps/web/src/app/(dashboard)/your-feature/
├── page.tsx              # Main page
├── page.test.tsx         # Tests
├── loading.tsx           # Loading state
└── components/
    ├── your-feature-card.tsx
    └── your-feature-form.tsx
```

### Page Component Pattern

```tsx
// apps/web/src/app/(dashboard)/your-feature/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export default function YourFeaturePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['your-feature', orgId],
    queryFn: () => api.get('/your-feature'),
  });

  if (isLoading) return <Skeleton />;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Your Feature</h1>
      {/* Content */}
    </div>
  );
}
```

### API Client

```typescript
// apps/web/src/lib/api.ts
export const api = {
  get: <T>(url: string) => fetch(`${API_BASE}${url}`).then(r => r.json()),
  post: <T>(url: string, data: any) => fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  patch: <T>(url: string, data: any) => /* ... */,
  delete: <T>(url: string) => /* ... */,
};
```

### Adding a Shared Component

```
apps/web/src/components/ui/your-component.tsx
apps/web/src/components/ui/your-component.test.tsx
```

---

## Testing

### Backend Tests

```bash
# Run all tests
cd apps/api
PYTHONPATH=. pytest tests/ -v

# Run specific test file
PYTHONPATH=. pytest tests/unit/test_your_test.py -v

# Run with coverage
PYTHONPATH=. pytest tests/ --cov=app --cov-report=html

# Run integration tests
PYTHONPATH=. pytest tests/integration/ -v
```

### Frontend Tests

```bash
# Run all tests
cd apps/web
pnpm test

# Run with UI
pnpm test:ui

# Run specific test
pnpm test your-component.test.tsx
```

### Writing Tests

```python
# Unit test example
import pytest
from uuid import uuid4
from app.domain.entities.your_entity import YourEntity

class TestYourEntity:
    def test_creation(self):
        entity = YourEntity(
            organization_id=uuid4(),
            name="Test"
        )
        assert entity.name == "Test"
    
    def test_to_dict(self):
        entity = YourEntity(name="Test")
        d = entity.to_dict()
        assert d["name"] == "Test"
```

```typescript
// Frontend test example
import { render, screen } from '@testing-library/react';
import { YourComponent } from '@/components/ui/your-component';

describe('YourComponent', () => {
  it('renders correctly', () => {
    render(<YourComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Test Fixtures (conftest.py)

```python
# apps/api/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = sessionmaker(engine, class_=AsyncSession)()
    yield session
    await session.close()
```

---

## Database

### Migrations

```bash
# Create new migration
cd apps/api
alembic revision --autogenerate -m "add your table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show history
alembic history
```

### Seed Data

```bash
cd apps/api
python scripts/seed_db.py
```

### Common Patterns

```python
# JSON columns
from sqlalchemy import JSON

class YourModel(Base):
    data = Column(JSON, default=dict)

# UUID columns
from sqlalchemy.dialects.postgresql import UUID
import uuid

id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Enums
from sqlalchemy import Enum
import enum

class Status(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

status = Column(Enum(Status), default=Status.ACTIVE)
```

---

## Debugging

### Backend Debugging

```bash
# VS Code launch.json
{
  "type": "python",
  "request": "launch",
  "name": "Debug FastAPI",
  "module": "uvicorn",
  "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
  "cwd": "${workspaceFolder}/apps/api",
  "env": {
    "PYTHONPATH": "${workspaceFolder}/apps/api"
  }
}
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Set `PYTHONPATH=apps/api` |
| `ImportError` | Check `__init__.py` files exist |
| `Database locked` | Ensure only one process uses SQLite |
| `Redis connection failed` | Check Redis is running on port 6379 |
| `Port already in use` | `lsof -i :8000` then kill |

### Database Debugging

```bash
# Connect to PostgreSQL
psql postgresql://astra:astra_dev@localhost:5432/astra

# Query directly
SELECT * FROM campaigns WHERE organization_id = '...';

# Check migrations
alembic current
alembic history
```

---

## Code Quality

### Linting

```bash
# Backend
cd apps/api
ruff check .
ruff format .

# Frontend
cd apps/web
pnpm lint
pnpm format
```

### Type Checking

```bash
# Backend
cd apps/api
mypy app/

# Frontend
cd apps/web
pnpm typecheck
```

### Pre-commit Hooks

```bash
# Install
pre-commit install

# Run manually
pre-commit run --all-files
```

### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, fastapi, sqlalchemy]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
```

---

## CI/CD

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          cd apps/api
          PYTHONPATH=. pytest tests/ -v --cov=app --cov-fail-under=80
      
      - name: Lint
        run: |
          cd apps/api
          ruff check .
          ruff format --check .
      
      - name: Type check
        run: |
          cd apps/api
          mypy app/

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      
      - name: Install dependencies
        run: |
          cd apps/web
          pnpm install
      
      - name: Run tests
        run: |
          cd apps/web
          pnpm test --run
      
      - name: Lint
        run: |
          cd apps/web
          pnpm lint
          pnpm format --check
      
      - name: Type check
        run: |
          cd apps/web
          pnpm typecheck
```

---

## Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ImportError: cannot import name` | Circular import | Refactor to remove circular dependency |
| `sqlalchemy.exc.OperationalError` | DB connection failed | Check DB running, check credentials |
| `pydantic.ValidationError` | Invalid input data | Check request payload matches schema |
| `asyncpg.exceptions.UniqueViolationError` | Duplicate unique key | Handle conflict in use case |
| `redis.exceptions.ConnectionError` | Redis unavailable | Check Redis service |
| `ModuleNotFoundError: app` | PYTHONPATH not set | Export PYTHONPATH=apps/api |

### Performance Issues

| Symptom | Investigation |
|---------|---------------|
| Slow API | Check DB query plans, add indexes |
| High memory | Profile with `py-spy` |
| Slow queries | `EXPLAIN ANALYZE` |
| High CPU | Check for infinite loops, profiling |

### Logs

```bash
# Application logs
docker logs -f astra-api

# Database logs
docker logs -f astra-postgres

# Redis logs
docker logs -f astra-redis

# Kubernetes
kubectl logs -f deployment/astra-api -n astra
```

---

## Useful Commands

```bash
# Makefile shortcuts (create Makefile in root)
make test           # Run all tests
make lint           # Lint all code
make typecheck      # Type check
make format         # Format code
make migrate        # Run migrations
make seed           # Seed database
make dev            # Start all dev servers
make build          # Build Docker images
make deploy         # Deploy to staging
```

---

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Next.js 15 Docs](https://nextjs.org/docs)
- [React 19 Docs](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TanStack Query](https://tanstack.com/query/latest)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [PostgreSQL 16 Docs](https://www.postgresql.org/docs/16/)
- [Redis 7 Docs](https://redis.io/docs/latest/)
- [Kubernetes Docs](https://kubernetes.io/docs/home/)

---

*This guide is updated regularly. Check for updates before starting new features.*