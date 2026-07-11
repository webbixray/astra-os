# ASTRA OS — Task Specification: M0 Foundation Completion

**Milestone**: M0 Foundation  
**Target Date**: 2026-07-31  
**Status**: 🟡 In Progress  
**Owner**: Platform Team  
**Session**: This document updated at start of each session per SESSION_BOOTSTRAP.md

---

## 1. Current Sprint Objective

Complete all M0 Foundation epics to achieve **deployable, testable, documented foundation** enabling M1 Agent Core development.

**Definition of Done for M0**:
- `make bootstrap` spins up full stack in <5 minutes on clean clone
- CI pipeline (8 jobs) passes on `main` branch
- `main` branch deployable to staging with single merge
- All 10 M0 epics at 100% with exit criteria verified

---

## 2. Epic Status & Remaining Work

### E0.1 Monorepo & Tooling ✅ **DONE**
- [x] Turborepo config (`turbo.json`)
- [x] pnpm workspace (`pnpm-workspace.yaml`)
- [x] Shared ESLint (`packages/config-eslint`)
- [x] Shared TypeScript (`packages/config-typescript`)
- [x] Shared Tailwind (`packages/config-tailwind`)
- [x] Shared UI components (`packages/ui`)

### E0.2 CI/CD Pipeline ✅ **DONE**
- [x] `.github/workflows/ci.yml` (8 jobs: api-test, api-lint, web-test, web-build, security, docker-build, deploy-staging)
- [x] `.github/workflows/docker.yml`
- [x] `.github/workflows/release.yml`
- [x] Conventional commits enforced
- [x] Semantic release configured

### E0.3 Docker & K8s 🟡 **80% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| Multi-stage Dockerfile (api) | ✅ | `apps/api/Dockerfile`, `apps/api/Dockerfile.dev` |
| Multi-stage Dockerfile (web) | ✅ | `apps/web/Dockerfile`, `apps/web/Dockerfile.dev` |
| `docker-compose.yml` (base) | ✅ | Postgres, Redis, Temporal, MinIO |
| `docker-compose.dev.yml` | ✅ | Hot reload, debug ports, Mailhog |
| `docker-compose.prod.yml` | ❌ | **MISSING** — production profile |
| K8s base manifests | 🟡 60% | `k8s/base/` exists, needs: HPA, NetworkPolicy, Servicemonitor |
| K8s overlays (local/preview/staging/prod) | ❌ | **MISSING** — only base exists |
| ExternalSecrets operator config | ❌ | **MISSING** |

**Blocking M0 Exit**: Production docker-compose, K8s overlays, ExternalSecrets

### E0.4 Authentication 🟡 **60% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| Supabase client setup (api) | ✅ | `apps/api/app/core/auth.py` |
| JWT middleware (FastAPI) | ✅ | `apps/api/app/middleware/auth.py` |
| Casbin RBAC enforcement | ❌ | **MISSING** — policy model + enforcer |
| Supabase Auth UI (web) | 🟡 50% | Login page exists, needs: signup, password reset, MFA |
| Session management | ✅ | HttpOnly cookies, refresh rotation |
| Tenant resolution middleware | ❌ | **MISSING** — `X-Tenant-ID` / subdomain extraction |
| RLS policies (PostgreSQL) | ❌ | **MISSING** — need migration + policies per table |

**Blocking M0 Exit**: Casbin RBAC, tenant resolution, RLS policies

### E0.5 Database Layer 🟡 **70% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| PostgreSQL + pgvector (compose) | ✅ | `docker-compose.yml` |
| Redis (compose) | ✅ | |
| Alembic config | ✅ | `apps/api/alembic.ini` |
| Base migration (tenants, users) | ✅ | `apps/api/alembic/versions/001_initial.py` |
| pgvector migration | ✅ | `apps/api/alembic/versions/002_pgvector.py` |
| Audit log table (partitioned) | ❌ | **MISSING** — per ARCHITECTURE.md §4.1 |
| Outbox table | ❌ | **MISSING** — per ARCHITECTURE.md §4.1 |
| Embeddings table + HNSW index | ❌ | **MISSING** — per ARCHITECTURE.md §4.2 |
| RLS policies migration | ❌ | **MISSING** — depends on E0.4 |
| Seed script (dev data) | 🟡 50% | `apps/api/scripts/seed_db.py` exists, incomplete |

**Blocking M0 Exit**: Audit/outbox/embeddings tables, RLS, complete seed

### E0.6 Clean Architecture Backbone 🟡 **50% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| Domain layer structure | ✅ | `apps/api/app/domain/` with entities, VOs, events |
| Application layer (use cases) | 🟡 40% | `apps/api/app/application/` — partial |
| Infrastructure layer (adapters) | 🟡 30% | `apps/api/app/infrastructure/` — repos partial |
| Presentation layer (routes) | 🟡 40% | `apps/api/app/presentation/` — health only |
| Dependency injection container | ❌ | **MISSING** — need `dependency-injector` or similar |
| Module structure per feature | 🟡 50% | Some features have full structure, others skeleton |

**Blocking M0 Exit**: DI container, complete module template

### E0.7 API Gateway 🟡 **40% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| FastAPI app factory | ✅ | `apps/api/app/main.py` |
| Health endpoints (`/health`, `/ready`) | ✅ | |
| OpenAPI generation | ✅ | `/openapi.json` |
| CORS middleware | ✅ | |
| Request ID middleware | ✅ | |
| Structured logging (JSON) | 🟡 50% | Basic setup, needs correlation IDs |
| Audit middleware | ❌ | **MISSING** — log every mutating request |
| Rate limiting | ❌ | **MISSING** — `slowapi` or similar |
| API versioning (`/api/v1/`) | ❌ | **MISSING** — router prefix |
| Error handling (RFC 7807) | ❌ | **MISSING** — problem details |

**Blocking M0 Exit**: Audit middleware, rate limiting, versioning, error format

### E0.8 Frontend Shell 🟡 **60% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| Next.js 15 + App Router | ✅ | `apps/web/` |
| shadcn/ui design system | ✅ | `packages/ui/` |
| Layout (sidebar, header, navigation) | ✅ | `apps/web/src/app/layout.tsx` |
| Auth pages (login) | ✅ | `apps/web/src/app/(auth)/login/` |
| Protected route wrapper | ✅ | `apps/web/src/middleware.ts` |
| API client (generated) | ❌ | **MISSING** — `openapi-typescript-codegen` |
| React Query setup | ✅ | `apps/web/src/lib/query.ts` |
| Zustand store (auth, tenant) | 🟡 50% | Partial |
| Tenant switcher UI | ❌ | **MISSING** |
| Error boundaries | ❌ | **MISSING** |
| Storybook | ❌ | **MISSING** |

**Blocking M0 Exit**: Generated API client, tenant switcher, error boundaries

### E0.9 Observability ⏳ **10% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| OpenTelemetry SDK (Python) | ❌ | **MISSING** |
| OpenTelemetry SDK (Node) | ❌ | **MISSING** |
| Prometheus metrics endpoint | ❌ | **MISSING** — `/metrics` |
| Grafana dashboards (JSON) | ❌ | **MISSING** |
| Loki log aggregation | ❌ | **MISSING** |
| Tempo trace backend | ❌ | **MISSING** |
| Health check endpoints (detailed) | 🟡 50% | Basic only |
| SLO dashboards | ❌ | **MISSING** |

**Blocking M0 Exit**: All observability — required for M1 agent tracing

### E0.10 Developer Experience 🟡 **70% — NEEDS WORK**
| Task | Status | Notes |
|------|--------|-------|
| `make bootstrap` script | 🟡 80% | `scripts/setup.sh` exists, needs validation |
| `make dev` (all services) | ✅ | `docker compose up` + `pnpm dev` |
| `make test` (all) | ✅ | Runs pytest + vitest + playwright |
| `make lint` | ✅ | Ruff + ESLint |
| `make typecheck` | ✅ | mypy + tsc |
| `make db-migrate` | ✅ | Alembic wrapper |
| `.env.example` complete | ✅ | |
| Seed script complete | 🟡 50% | Incomplete |
| Documentation published | ✅ | ENGINEERING_CONSTITUTION, PRODUCT_VISION, ARCHITECTURE, SESSION_BOOTSTRAP, ROADMAP |

**Blocking M0 Exit**: Validate `make bootstrap` end-to-end, complete seed script

---

## 3. Prioritized Task List for Current Session

### P0 — Must Complete This Session (Blocking M0 Exit)

| # | Task | Epic | Est. Hours | Assignee |
|---|------|------|------------|----------|
| 1 | Create `docker-compose.prod.yml` with: resource limits, secrets, healthchecks, replica counts | E0.3 | 2 | Platform |
| 2 | Create K8s overlays: `k8s/overlays/{local,preview,staging,production}` with kustomize | E0.3 | 3 | Platform |
| 3 | Implement Casbin RBAC enforcer + policy model (Casbin) | E0.4 | 3 | Backend |
| 4 | Add tenant resolution middleware (header + subdomain) | E0.4 | 1 | Backend |
| 5 | Create RLS migration + policies for all tenant-scoped tables | E0.4/0.5 | 2 | Backend |
| 6 | Add audit log table (partitioned) + outbox table + embeddings table migrations | E0.5 | 2 | Backend |
| 7 | Complete seed script with realistic dev data (10 campaigns, 5 agents, etc.) | E0.5 | 1 | Backend |
| 8 | Implement dependency injection container (`dependency-injector`) | E0.6 | 2 | Backend |
| 9 | Add audit middleware (log mutating requests with user/tenant/action) | E0.7 | 1 | Backend |
| 10 | Add rate limiting (`slowapi`) + API versioning (`/api/v1/`) | E0.7 | 1 | Backend |
| 11 | Add RFC 7807 problem detail error handler | E0.7 | 1 | Backend |
| 12 | Generate TypeScript API client from OpenAPI spec | E0.8 | 1 | Frontend |
| 13 | Build tenant switcher component + store | E0.8 | 1 | Frontend |
| 14 | Add React error boundaries + global error page | E0.8 | 1 | Frontend |

### P1 — Should Complete This Session (Unblocks M1)

| # | Task | Epic | Est. Hours |
|---|------|------|------------|
| 15 | OpenTelemetry Python instrumentation (FastAPI, SQLAlchemy, Redis, HTTPX) | E0.9 | 2 |
| 16 | OpenTelemetry Node instrumentation (Next.js) | E0.9 | 2 |
| 17 | Prometheus `/metrics` endpoint + key metrics (request duration, db pool, queue depth) | E0.9 | 1 |
| 18 | Grafana dashboard JSONs (System, API, Business) | E0.9 | 2 |
| 19 | Loki + Tempo docker-compose integration | E0.9 | 1 |
| 20 | Validate `make bootstrap` on clean VM/container | E0.10 | 1 |

### P2 — Can Defer to Next Session

| # | Task | Epic |
|---|------|------|
| 21 | Storybook setup for UI package | E0.8 |
| 22 | ExternalSecrets operator + SecretStore manifests | E0.3 |
| 23 | MFA + password reset flows (Supabase) | E0.4 |
| 24 | Complete feature module template (cookiecutter) | E0.6 |
| 25 | Load test script (k6) for API baseline | E0.9 |

---

## 4. Quality Gates for This Session

Before marking any P0 task complete, verify:

- [ ] **Lint**: `make lint` passes (ruff, eslint)
- [ ] **Typecheck**: `make typecheck` passes (mypy, tsc)
- [ ] **Unit Tests**: New code has tests; `make test` passes
- [ ] **Integration**: DB migrations apply + rollback cleanly
- [ ] **Documentation**: Updated ARCHITECTURE.md if schema changed; ADR if architectural
- [ ] **Conventional Commit**: `feat(scope): description` format

---

## 5. Session Log

### Session 2026-07-12
**Started**: 2026-07-12 00:00 UTC
**Context Loaded**: ENGINEERING_CONSTITUTION, PRODUCT_VISION, ARCHITECTURE, ROADMAP, TASK_SPEC
**Repository State**:
- Branch: `main` (clean)
- Last commit: `fix: resolve M0 foundation blockers`
- CI: Pending push

**Work Completed**:
- [x] Removed hardcoded `file:///app/...` dependency for agent_orchestrator from pyproject.toml
- [x] Installed orchestrator as editable package in Dockerfile.dev (`uv pip install -e`)
- [x] Added orchestrator install to `scripts/setup.sh` for local dev
- [x] Fixed `release.yml` to reference `Dockerfile` instead of non-existent `Dockerfile.prod`
- [x] Raised CI coverage threshold from 60% to 80% per Engineering Constitution §10.2
- [x] Removed `continue-on-error` from security audit in CI pipeline per Constitution §5.2
- [x] Fixed docker-compose.yml build context (`.`) and volume mounts (`./` not `../`)
- [x] Added sys.path fix in alembic/env.py for cross-directory imports
- [x] Added `services/*` to pnpm workspace for monorepo integration
- [x] Added agent_orchestrator package to services/ (12 files)
- [x] Fixed duplicate import in alembic/env.py
- [x] Validated all YAML, JSON, TOML, Python syntax
- [x] Verified Dockerfiles pass BuildKit validation
- [x] Verified K8s manifests (multi-doc YAML + kustomization files)

**Next Actions**:
1. Push to origin and verify CI passes
2. Complete remaining M0 P0 tasks (DI container, seed script, observability)
3. Validate `make bootstrap` end-to-end on clean clone
4. Begin M1 Agent Core epic breakdown

---

## 6. Next Session Priorities (Update at End)

1. Complete remaining P0 tasks from above
2. Validate `make bootstrap` end-to-end
3. Run full CI pipeline locally (`act` or push to trigger)
4. Begin M1 Agent Core epic breakdown

---

## 7. Blockers & Escalations

| Blocker | Impact | Owner | Resolution Target |
|---------|--------|-------|-------------------|
| None currently | — | — | — |

---

**End of Task Spec**

*Update this file at end of each session. Commit with `chore(task-spec): update M0 progress`*