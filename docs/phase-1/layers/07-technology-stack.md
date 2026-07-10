# Phase 1.9: Technology Stack Finalization

## Finalized Stack

### Frontend

| Technology | Version | Purpose | Justification |
|---|---|---|---|
| **Next.js** | 15.x | React framework | App Router, RSC, streaming SSR, file-based routing |
| **React** | 19.x | UI library | Industry standard, large ecosystem |
| **TypeScript** | 5.x | Type safety | Strict mode enabled |
| **Tailwind CSS** | 4.x | Styling | Utility-first, rapid iteration, dark mode |
| **shadcn/ui** | latest | Component library | Accessible, customizable, not a dependency |
| **TanStack Query** | 5.x | Server state | Caching, optimistic updates, WebSocket sync |
| **Zustand** | 5.x | Client state | Lightweight, middleware, no boilerplate |
| **React Hook Form** | 7.x | Forms | Performant, minimal re-renders |
| **Zod** | 3.x | Schema validation | TypeScript-first, shared with backend |
| **Framer Motion** | 11.x | Animation | Declarative, gesture support |
| **React Flow** | 11.x | Flow builder | Node-based UI for workflow engine |
| **Recharts** | 2.x | Charts | Composable React charting |
| **TipTap** | 2.x | Rich text editor | ProseMirror-based, extensible |

### Backend

| Technology | Version | Purpose | Justification |
|---|---|---|---|
| **Python** | 3.12+ | Runtime | Async support, ML ecosystem |
| **FastAPI** | 0.115+ | API framework | Async, OpenAPI auto-generation, Pydantic |
| **Pydantic** | 2.x | Validation | Type-safe, serialization, settings management |
| **SQLAlchemy** | 2.x | ORM | Mature, async support, Alembic integration |
| **Alembic** | 1.x | Migrations | Declarative, reversible migrations |
| **Celery** | 5.x | Task queue | Async task processing |
| **Redis** | 7.x | Cache/Queue/PubSub | Multi-purpose, fast, well-understood |
| **PostgreSQL** | 16.x | Database | ACID, JSONB, pgvector, proven at scale |

### AI & Agents

| Technology | Version | Purpose | Justification |
|---|---|---|---|
| **Temporal** | 1.x | Workflow durability | Battle-tested at Uber/Netflix |
| **NVIDIA NIM** | latest | Self-hosted LLM inference | Predictable latency/cost |
| **OpenAI API** | latest | LLM fallback | Industry standard |
| **Anthropic API** | latest | LLM fallback | Best for complex reasoning |
| **Gemini API** | latest | LLM fallback | Cost-effective for simple tasks |
| **pgvector** | 0.7+ | Vector storage | PostgreSQL extension, no separate DB |
| **LangChain** | 0.3+ | LLM abstractions | Prompt templates, output parsing (not agent framework) |

### Infrastructure

| Technology | Version | Purpose | Justification |
|---|---|---|---|
| **Docker** | latest | Containerization | Industry standard |
| **Kubernetes** | 1.30+ | Orchestration | Production scaling |
| **GitHub Actions** | - | CI/CD | Native GitHub integration |
| **Prometheus** | latest | Metrics | CNCF standard |
| **Grafana** | latest | Dashboards | Rich visualization |
| **OpenTelemetry** | latest | Tracing | Vendor-neutral observability |
| **Nginx** | latest | Reverse proxy | Battle-tested |
| **HashiCorp Vault** | latest | Secrets management | Enterprise security |

### Testing

| Technology | Purpose |
|---|---|
| **Pytest** | Python unit/integration tests |
| **Vitest** | TypeScript unit tests |
| **Playwright** | E2E browser tests |
| **pytest-cov** | Python coverage |
| **istanbul/nyc** | TypeScript coverage |

## Package Versions (Initial)

### Python Dependencies (requirements.txt / pyproject.toml)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
pydantic-settings>=2.4.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.30.0
alembic>=1.13.0
redis[hiredis]>=5.1.0
celery>=5.4.0
temporalio>=1.8.0
httpx>=0.27.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
sentry-sdk[fastapi]>=2.10.0
opentelemetry-api>=1.26.0
opentelemetry-sdk>=1.26.0
opentelemetry-instrumentation-fastapi>=0.47b0
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-anthropic>=0.2.0
```

### TypeScript Dependencies (package.json)

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.50.0",
    "zustand": "^5.0.0",
    "react-hook-form": "^7.52.0",
    "zod": "^3.23.0",
    "framer-motion": "^11.3.0",
    "reactflow": "^11.11.0",
    "recharts": "^2.12.0",
    "@tiptap/react": "^2.6.0",
    "@tiptap/starter-kit": "^2.6.0",
    "lucide-react": "^0.400.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.4.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "@types/react": "^19.0.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^4.0.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.0.0",
    "prettier": "^3.3.0",
    "prettier-plugin-tailwindcss": "^0.6.0",
    "vitest": "^2.0.0",
    "playwright": "^1.45.0",
    "@playwright/test": "^1.45.0"
  }
}
```

## Code Quality Tooling

| Tool | Purpose | Configuration |
|---|---|---|
| **ESLint** | JS/TS linting | Strict config, no unused vars |
| **Prettier** | Code formatting | 2 spaces, 100 char width |
| **Ruff** | Python linting | All rules enabled, auto-fix |
| **mypy** | Python type checking | Strict mode |
| **pyright** | Python type checking | Pylance-compatible |
| **isort** | Python import sorting | Black-compatible |
| **pre-commit** | Pre-commit hooks | Lint + format + type-check |
| **husky** | Git hooks | Pre-commit + pre-push |

## Monorepo Tooling

| Tool | Version | Purpose |
|---|---|---|
| **pnpm** | 9.x | Package manager (frontend) |
| **Turborepo** | 2.x | Build system |
| **uv** | latest | Python package manager |
| **Docker Compose** | 2.x | Local development |
| **Just** | latest | Command runner (Make alternative) |

## Key Constraints

1. **No vendor lock-in** — AI models, cloud provider, vector DB all have abstraction layers
2. **No deprecated packages** — all dependencies must be actively maintained
3. **Minimal dependencies** — prefer standard library over external packages
4. **TypeScript strict mode** — always
5. **Python type hints** — 100% coverage, mypy strict
6. **Docker images** — distroless base images where possible
7. **Lock files** — pnpm-lock.yaml, requirements.txt hash checking
