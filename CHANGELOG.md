# ASTRA OS — Changelog

**Version**: 1.0  
**Format**: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
**Versioning**: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

### Added
- Shadow Mode (E6.2): Agent/human decision comparison with lift measurement
- Observability Suite (E6.4): Metrics, alerting, cost tracking, SLA monitoring, dashboards
- Social Intelligence (E6.1): Comment monitoring, AI auto-reply, moderation
- Sample Campaigns API for onboarding
- Enhanced Setup Wizard with sample campaigns step

### Changed
- Auth routes: ValidationError now properly returns 422 instead of 500
- Workflow canvas: Enhanced with execution viewer tab

### Fixed
- CronExpression weekday mapping (Python vs cron convention)
- Auth integration test failures (4 tests)

---

## [0.0.1] - 2024-07-12

### Added - M5 Workflow Engine

#### Backend
- **Workflow Scheduler**: Cron, event-driven, webhook, manual triggers
- **Workflow Templates**: 4 built-in (Campaign Launch, Creative Review, Optimization Loop, Brand Compliance)
- **Workflow Versioning**: Immutable snapshots, restore, compare, replay debugging
- **API Routes**: Template CRUD, instantiation, version management, replay

#### Frontend
- **Template Gallery**: `/workflows/templates` with category filtering
- **Execution Viewer**: Step-by-step execution status with icons
- **Enhanced Detail Page**: Builder / Executions tabs
- **API Hooks**: useWorkflowTemplates, useInstantiateTemplate, useWorkflowExecutions

#### Tests
- 57 Scheduler tests (cron parsing, triggers, lifecycle)
- 25 Template tests (creation, instantiation, registry)
- 10 Versioning tests (create, restore, compare, replay)

### Added - M4 Intelligence (Previous)

#### Core Intelligence Services
- **RAG Pipeline**: Hybrid search (vector + keyword), context assembly
- **Predictive Optimization**: Budget allocation, creative fatigue, audience expansion
- **Cross-Campaign Learning**: Pattern mining, transfer learning

#### API Routes
- 4 RAG endpoints (query, context, search, ingest)
- 4 Optimization endpoints (budget, fatigue, audience, cross-campaign)
- 3 Cross-campaign endpoints (patterns, transfer, insights)

#### Frontend
- RAG Search UI with brand guidelines ingestion
- Optimization Dashboard (budget, fatigue, audience tabs)
- Knowledge Graph Visualization

#### Tests
- 33 RAG tests
- 23 Optimization tests
- 17 Cross-campaign tests
- 12 Route integration tests
- 9 Agent RAG integration tests

### Added - M3 Governance (Previous)

- Approval Engine (spend, brand, audience rules)
- Autonomy Levels (0=Advisory, 1=Semi-auto, 2=Full-auto)
- Audit & Compliance (immutable log, export, retention)
- Explainability (reasoning trace, natural language summaries)
- Agent Governance Middleware (runtime enforcement)

### Added - M2 Campaign Execution (Previous)

- Campaign Domain (CRUD, lifecycle, budget pacing)
- Meta Ads Adapter (full lifecycle sync)
- Creative Management (assets, variants, approval)
- Frontend Campaign Builder

### Added - M1 Agent Core (Previous)

- Agent Runtime (base class, registry, hierarchy)
- Model Router (NVIDIA NIM → OpenAI → Anthropic → Gemini)
- Memory System (working, episodic, semantic)
- Agent Hierarchy (CEO → 7 Directors → Specialists)

### Added - M0 Foundation (Previous)

- Monorepo (Turborepo, pnpm workspace)
- CI/CD Pipeline (GitHub Actions: lint, typecheck, test, build, docker)
- Docker & K8s (multi-stage, Kustomize)
- Auth (Supabase JWT, RBAC, feature flags)
- Database (PostgreSQL + pgvector, Alembic, RLS)
- Clean Architecture (Domain/Application/Infrastructure/Presentation)
- API Gateway (FastAPI, health, OpenAPI, rate limiting)
- Frontend Shell (Next.js 15, App Router, shadcn/ui)

---

## Release Notes Format

Each release includes:
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

---

## Upgrade Guide

### From 0.0.1 to 0.0.2 (Upcoming)

```bash
# 1. Pull latest
git pull origin main

# 2. Update dependencies
cd apps/api
pip install -e ".[dev]"
cd ../web
pnpm install

# 3. Run migrations
cd apps/api
alembic upgrade head

# 4. Restart services
# ... restart API and workers
```

### Breaking Changes

None in 0.0.1. All additions are backward compatible.

---

## Release Schedule

| Version | Target Date | Focus |
|---------|-------------|-------|
| 0.0.1 | 2024-07-12 | M0-M5 Complete |
| 0.1.0 | 2024-08-15 | E6.3 Self-Serve + E6.5 Docs |
| 0.2.0 | 2024-09-30 | E6.2 Shadow Mode Polish |
| 0.5.0 | 2024-12-15 | M6 Beta Launch |
| 1.0.0 | 2025-06-30 | M7 GA Release |

---

*Changelog maintained per release. See git log for detailed commit history.*