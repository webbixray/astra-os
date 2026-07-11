# Astra OS - Development Guide

Welcome to Astra OS! This guide will help you set up and start developing.

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/webbixray/astra-os.git
cd astra-os

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Start development
make dev
```

### Option 2: Manual Setup

```bash
# 1. Clone and install dependencies
git clone https://github.com/webbixray/astra-os.git
cd astra-os
pnpm install

# 2. Set up environment
cp docker/dev/.env .env
# Edit .env with your API keys

# 3. Start infrastructure
docker compose up -d postgres redis temporal

# 4. Install Python dependencies
cd apps/api
pip install -e ".[dev]"

# 5. Run migrations
alembic upgrade head

# 6. Seed database (optional)
python -m scripts.seed_db

# 7. Start development servers
cd ../..
pnpm dev
```

### Option 3: Docker-First Development

```bash
# Start everything with Docker
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Prerequisites

- **Node.js** >= 20.0.0
- **pnpm** >= 9.0.0
- **Python** >= 3.12
- **Docker** (recommended)
- **PostgreSQL** 16 (or use Docker)
- **Redis** 7 (or use Docker)

## Project Structure

```
astraos/
├── apps/
│   ├── api/              # Python/FastAPI backend
│   └── web/              # Next.js frontend
├── packages/
│   ├── shared/           # Shared TypeScript types
│   ├── ui/               # Shared UI components
│   ├── config-eslint/    # ESLint configs
│   ├── config-typescript/# TypeScript configs
│   └── config-tailwind/  # Tailwind configs
├── docker/               # Docker configurations
├── k8s/                  # Kubernetes manifests
├── scripts/              # Development scripts
└── docs/                 # Documentation
```

## Development Commands

### Using Make

```bash
make help              # Show all available commands
make dev               # Start all services
make test              # Run all tests
make lint              # Lint code
make format            # Format code
make db-migrate msg="add feature"  # Create migration
make docker-up         # Start Docker services
```

### Using pnpm

```bash
pnpm dev               # Start all dev servers
pnpm build             # Build all packages
pnpm test              # Run all tests
pnpm lint              # Lint all code
pnpm typecheck         # Type check all code
pnpm format            # Format all code
```

### API Development

```bash
cd apps/api

# Start API server
uvicorn app.main:app --reload

# Run tests
python -m pytest -v

# Run tests with coverage
python -m pytest --cov=app --cov-report=html

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Seed database
python -m scripts.seed_db
```

### Frontend Development

```bash
cd apps/web

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npx vitest run

# Run E2E tests
npx playwright test

# Lint
next lint
```

## Environment Variables

Copy `docker/dev/.env.example` to `.env` and configure:

### Required

```env
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=postgresql+asyncpg://astra:astra_dev@localhost:5432/astra
REDIS_URL=redis://localhost:6379/0
```

### AI Providers (at least one recommended)

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

### Ad Platforms (optional)

```env
GOOGLE_ADS_CLIENT_ID=...
META_ACCESS_TOKEN=...
LINKEDIN_ACCESS_TOKEN=...
TIKTOK_ACCESS_TOKEN=...
```

## Database

### Migrations

```bash
# Create a new migration
cd apps/api
alembic revision --autogenerate -m "add user preferences"

# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check current version
alembic current
```

### Seeding

```bash
# Seed with sample data
cd apps/api
python -m scripts.seed_db
```

## Testing

### Unit Tests

```bash
# Run all tests
make test

# Run API tests only
make test-api

# Run Web tests only
make test-web

# Run with coverage
make test-cov
```

### E2E Tests

```bash
# Install Playwright browsers
cd apps/web
npx playwright install

# Run E2E tests
npx playwright test

# Run specific test
npx playwright test login.spec.ts

# Open Playwright UI
npx playwright ui
```

## Docker

### Development

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f api

# Stop services
docker compose down

# Rebuild after changes
docker compose up -d --build
```

### Production

```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Start production stack
docker compose -f docker-compose.prod.yml up -d
```

## Kubernetes

### Deployment

```bash
# Deploy to cluster
kubectl apply -k k8s/

# Check status
kubectl get pods -n astra

# View logs
kubectl logs -f deployment/astra-api -n astra

# Scale API
kubectl scale deployment/astra-api --replicas=5 -n astra

# Delete deployment
kubectl delete -k k8s/
```

## Code Style

### Python

- **Formatter**: Ruff
- **Linter**: Ruff
- **Type Checker**: mypy
- **Max Line Length**: 100

```bash
# Format
cd apps/api
ruff format .

# Lint
ruff check .

# Type check
mypy . --ignore-missing-imports
```

### TypeScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checker**: TypeScript

```bash
# Format
pnpm format

# Lint
pnpm lint

# Type check
pnpm typecheck
```

## IDE Setup

### VS Code

Install recommended extensions:
- Python
- Prettier
- ESLint
- Tailwind CSS IntelliSense

### Cursor / Windsurf

The project includes `.cursorrules` for AI-assisted development.

## Troubleshooting

### Port already in use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database connection refused

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Migration conflicts

```bash
# Check for multiple heads
alembic heads

# Merge heads
alembic merge heads

# Apply merged migration
alembic upgrade head
```

### Clear all data

```bash
# Reset database
docker compose down -v
docker compose up -d postgres
cd apps/api
alembic upgrade head
python -m scripts.seed_db
```

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests: `make test`
4. Run linter: `make lint`
5. Commit changes: `git commit -m "feat: add my feature"`
6. Push to branch: `git push origin feature/my-feature`
7. Create a Pull Request

## Architecture

See `docs/phase-1/` for detailed architecture documentation:

- ADR-001: Monorepo Architecture
- ADR-002: Clean Architecture
- ADR-003: Agent Orchestration
- ADR-004: Workflow Engine
- ADR-005: Database Design
- ADR-006: Model Router
- ADR-007: Next.js Frontend
- ADR-008: Authentication
- ADR-009: Event-Driven Architecture

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Docs**: `docs/` directory

## License

Proprietary - See LICENSE file
