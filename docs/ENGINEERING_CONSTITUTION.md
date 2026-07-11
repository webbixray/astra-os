# ASTRA OS — Engineering Constitution

**Version**: 1.0.0  
**Status**: Immutable — Requires Architecture Review Board approval to amend  
**Effective Date**: 2026-07-11

---

## Preamble

ASTRA OS is an enterprise-grade AI operating system for marketing organizations. This Constitution establishes the immutable engineering principles, architectural mandates, quality gates, and governance processes that govern all development. No feature, refactor, or hotfix may violate these principles without explicit Architecture Review Board (ARB) approval.

---

## Article I: Foundational Principles

### 1.1 Professional Engineering Discipline
We operate as a Tier-1 software company. Every change undergoes the full SDLC: discovery → design → implementation → review → test → deploy → observe. No phase is optional.

### 1.2 Architecture Governance
- **Architecture Decision Records (ADRs)** are mandatory for all architectural decisions (ADR-001 through ADR-009 are ratified)
- **Architecture Review Board (ARB)**: CTO, Chief Architect, Principal Engineer, Security Architect — quorum of 3 required
- **Architectural drift is technical debt** — detected automatically via archunit tests in CI

### 1.3 Quality Is Non-Negotiable
A change is not "done" until it passes all quality gates:
- Static analysis (lint, type-check, security scan)
- Unit tests (≥80% coverage, branch coverage ≥70%)
- Integration tests (all critical paths)
- E2E tests (critical user journeys)
- Security scan (SAST + dependency audit)
- Performance benchmarks (no regression >5%)
- Accessibility audit (WCAG 2.1 AA)
- Documentation updated (ADR, API specs, runbooks)

### 1.4 Observability First
Every service must expose: health checks, structured logs (JSON), metrics (Prometheus), traces (OpenTelemetry), and audit logs for AI decisions.

### 1.5 Security by Default
- Zero-trust networking
- Secrets in vaults (never in repo, never in env files committed)
- All AI actions auditable with immutable logs
- Human approval required for: data export, external API calls, destructive actions, PII access

---

## Article II: Architecture Mandates

### 2.1 Clean Architecture (ADR-002)
**Backend (FastAPI)**: Four-layer separation — Presentation → Application → Domain → Infrastructure  
**Frontend (Next.js)**: Pages/Layouts → Features → Shared/UI → Lib/Utils

**Dependency Rule**: Inner layers never depend on outer layers. Dependency inversion via interfaces/ports.

### 2.2 Domain-Driven Design
- Feature-first module organization (ADR-001, ADR-002)
- Each domain module: `domain/`, `application/`, `infrastructure/`, `presentation/`, `tests/`
- Aggregates enforce invariants; domain events for cross-module communication

### 2.3 Hexagonal Architecture (Ports & Adapters)
- Domain defines **ports** (interfaces)
- Infrastructure provides **adapters** (PostgreSQL, Redis, NVIDIA NIM, Supabase, ad platforms)
- Application layer orchestrates via dependency injection

### 2.4 Event-Driven Architecture (ADR-009)
- Redis Pub/Sub + PostgreSQL LISTEN/NOTIFY for intra-service events
- Outbox pattern for reliable event publishing
- Event schema versioning via shared types package

### 2.5 API-First Development
- OpenAPI 3.1 specs defined **before** implementation
- Contract tests enforce provider/consumer compatibility
- Versioning via URL path (`/api/v1/`, `/api/v2/`)

### 2.6 AI Engineering Standards (ASTRA-Specific)
Per ADR-003, ADR-006:
- **Agent Orchestrator**: Custom hierarchical system (CEO → Directors → Specialists)
- **Model Router**: NVIDIA NIM primary → OpenAI → Anthropic → Gemini fallbacks
- **RAG**: pgvector for embeddings, hybrid search (vector + keyword)
- **Knowledge Graph**: Neo4j for entity-relationship reasoning
- **Memory**: Working (in-context), Episodic (PostgreSQL), Semantic (pgvector)
- **Tool Execution**: Sandbox with timeout, resource limits, audit logging
- **Human-in-the-Loop**: Required for destructive actions, PII, spend > $100
- **Explainability**: Every agent decision emits reasoning trace
- **Autonomy Levels**: Configurable per agent (0=advisory, 1=semi-auto, 2=full-auto with audit)

---

## Article III: Repository Governance

### 3.1 Branch Strategy (GitFlow + Trunk-Based Hybrid)
```
main          → protected, always deployable, tagged releases only
develop       → integration branch, CI must pass
feature/*     → one per issue, short-lived (<5 days), rebased onto develop
release/*     → stabilization, version bump, changelog, RC tags
hotfix/*      → from main, emergency fixes, fast-track to main + develop
```

### 3.2 Commit Discipline (Conventional Commits 1.0)
```
<type>(<scope>): <subject>

<type> ∈ {feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert}
<scope> = module name (campaigns, agents, workflows, etc.)
```
**Examples**:
```
feat(campaigns): add budget pacing algorithm
fix(agents): resolve memory leak in agent orchestrator
docs(adr): add ADR-010 event sourcing for campaigns
refactor(workflows)!: migrate to temporal workflow engine
```

### 3.3 Semantic Versioning (SemVer 2.0)
- MAJOR: Breaking API changes, schema migrations without backward compat
- MINOR: Backward-compatible features
- PATCH: Bug fixes, security patches
- Pre-release: `-rc.1`, `-beta.2`, `-alpha.1`

### 3.4 Pull Request Requirements
Every PR must include:
- Linked GitHub Issue with acceptance criteria
- Technical design (for features >2 SP)
- Checklist: tests, docs, lint, typecheck, security, migration
- At least 2 approvals (1 from domain owner, 1 from ARB for architectural changes)
- All CI gates passing
- Changelog entry (auto-generated from conventional commits)

### 3.5 GitHub Standards
- **Issues**: Template with problem, acceptance criteria, definition of done
- **Projects**: Kanban board per milestone (Backlog → Ready → In Progress → Review → Done)
- **Discussions**: Architecture decisions, RFCs, design reviews
- **ADRs**: Stored in `docs/adr/` with index in `ADR-INDEX.md`

---

## Article IV: Docker & Infrastructure Standards

### 4.1 Multi-Stage Dockerfiles
```dockerfile
# Build stage
FROM python:3.12-slim AS builder
# Install build deps, compile wheels, run tests

# Runtime stage
FROM python:3.12-slim AS runtime
# Copy only runtime artifacts, non-root user, healthcheck
```

### 4.2 Docker Compose Profiles
- `docker-compose.yml` — base infrastructure (PostgreSQL, Redis, Temporal, MinIO)
- `docker-compose.dev.yml` — dev overrides (hot reload, debug ports, mailhog)
- `docker-compose.prod.yml` — production (replicas, resources, secrets, monitoring)

### 4.3 Required Services (Development)
| Service | Purpose | Health Check |
|---------|---------|--------------|
| PostgreSQL 16 + pgvector | Primary DB, vectors | `pg_isready` |
| Redis 7 | Cache, queue, pub/sub | `redis-cli ping` |
| Temporal | Workflow durability | gRPC health check |
| MinIO (S3-compatible) | Object storage | `/minio/health/live` |
| NVIDIA NIM (local) | LLM inference | `/v1/health` |
| Mailhog | Email testing | HTTP 200 |

### 4.4 Single-Command Bootstrap
```bash
git clone <repo> && cd astra-os && make bootstrap
# Must: clone → install deps → start infra → migrate DB → seed → verify health
```

---

## Article V: CI/CD Pipeline (Quality Gates)

### 5.1 Pipeline Stages (All Required)

| Stage | Tools | Gate Criteria |
|-------|-------|---------------|
| **Lint/Format** | ruff, prettier, eslint | Zero violations |
| **Type Check** | mypy, tsc --noEmit | Zero errors |
| **Static Analysis** | bandit, trivy, semgrep | No HIGH/CRITICAL |
| **Unit Tests** | pytest, vitest | ≥80% line, ≥70% branch |
| **Integration Tests** | pytest + testcontainers | All critical paths pass |
| **E2E Tests** | playwright | All critical journeys pass |
| **Performance** | k6, locust | p95 < 200ms (API), < 3s (Web) |
| **Accessibility** | axe-core | WCAG 2.1 AA |
| **Build** | docker buildx | Multi-arch images, SBOM |
| **Security Scan** | trivy, snyk | Zero CRITICAL, 0 HIGH in prod deps |

### 5.2 Merge Policy
- **No merge if any gate fails** — no exceptions, no `continue-on-error`
- **Auto-merge** enabled after all checks + approvals
- **Deploy on merge to main** → staging → production (progressive)

### 5.3 Release Process
1. Create `release/vX.Y.Z` branch from `develop`
2. CI runs full pipeline + performance benchmarks
3. CHANGELOG.md generated from conventional commits
4. GitHub Release with artifacts, SBOM, release notes
5. Tag `vX.Y.Z` → triggers production deploy
6. Merge release branch → `main` + `develop`

---

## Article VI: Testing Standards

### 6.1 Test Pyramid (Enforced by CI)
- **Unit (70%)**: Pure domain logic, use cases, utilities — fast, isolated
- **Integration (20%)**: Repository adapters, external API clients, event handlers
- **E2E (10%)**: Critical user journeys (login → create campaign → launch)

### 6.2 Test Organization
```
tests/
├── unit/           # Domain, application layer
├── integration/    # Infrastructure adapters
├── e2e/            # Playwright (web), API contracts
├── contract/       # Pact/OpenAPI contract tests
├── performance/    # k6 scripts
├── accessibility/  # axe-core
└── fixtures/       # Shared test data builders
```

### 6.3 Test Data Management
- **No shared fixtures** — each test builds own data via builders/factories
- **Database per test** (testcontainers) or transaction rollback
- **Deterministic seeds** for property-based testing

### 6.4 AI-Specific Testing
- **Agent behavior tests**: Scenario-based, deterministic seeds
- **Prompt regression**: Golden master comparison
- **Tool execution**: Sandbox isolation, timeout, resource limits
- **Hallucination detection**: Fact-checking against knowledge graph

---

## Article VII: Documentation as Code

### 7.1 Documentation Structure
```
docs/
├── PRODUCT_VISION.md        # Business goals, personas, success metrics
├── ROADMAP.md               # Milestones, timeline, dependencies
├── ARCHITECTURE.md          # System context, container, component, code (C4)
├── ADR/
│   ├── ADR-INDEX.md
│   └── ADR-XXX-title.md
├── API/
│   ├── openapi.yaml         # Generated from code
│   └── changelog.md
├── DATABASE.md              # Schema, migrations, conventions
├── SECURITY.md              # Threat model, data classification, incident response
├── DEPLOYMENT.md            # Environments, runbooks, rollback procedures
├── RUNBOOKS/
│   ├── incident-response.md
│   ├── scaling.md
│   └── disaster-recovery.md
├── CONTRIBUTING.md          # Onboarding, workflow, standards
├── TESTING.md               # Strategy, tools, patterns
└── RELEASE_PROCESS.md       # Versioning, branching, hotfix procedure
```

### 7.2 Documentation Rules
- **Co-located**: Docs live with code (README.md per module, ADR per decision)
- **Generated**: API specs from code, DB docs from migrations, diagrams from code
- **Updated in same PR** — no "doc later" commits
- **Reviewed** — docs changes require technical writer or domain owner review

---

## Article VIII: AI Agent Governance (ASTRA-Specific)

### 8.1 Agent Lifecycle
1. **Specification** → ADR + Agent Spec (role, tools, memory, autonomy level)
2. **Implementation** → TDD with behavior scenarios
3. **Simulation** → Deterministic replay, chaos testing
4. **Shadow Mode** → Run alongside human, compare decisions
5. **Gradual Rollout** → Advisory → Semi-auto → Full-auto (per tenant config)
6. **Continuous Evaluation** → Drift detection, A/B testing, human feedback loops

### 8.2 Audit & Compliance
- Every agent action: timestamp, agent_id, input, reasoning, tool_calls, output, human_approval (if required)
- Immutable audit log (append-only PostgreSQL + WAL archival)
- Quarterly compliance review (GDPR, CCPA, SOC2)

### 8.3 Model Governance
- Model registry with versioning, provenance, evaluation metrics
- A/B testing framework for model routing
- Cost budgets per agent/tenant with alerts
- Fallback chains with SLA guarantees

---

## Article IX: Incident & Operational Excellence

### 9.1 Incident Response
- **Severity Levels**: SEV-1 (customer-facing outage), SEV-2 (degraded), SEV-3 (minor), SEV-4 (cosmetic)
- **On-call rotation**: Primary + secondary, 30-min acknowledgment SLA
- **Blameless postmortems** within 5 business days
- **Action items** tracked as GitHub issues with due dates

### 9.2 SLOs (Target)
| Service | Availability | Latency (p95) | Error Rate |
|---------|--------------|---------------|------------|
| API Gateway | 99.9% | <200ms | <0.1% |
| Agent Orchestrator | 99.5% | <5s | <1% |
| Workflow Engine | 99.9% | <1s | <0.1% |
| Frontend | 99.9% | <3s (LCP) | <0.1% |

### 9.3 Capacity Planning
- Load testing quarterly
- Auto-scaling policies defined per service
- Chaos engineering monthly (Litmus/Gremlin)

---

## Article X: Amendment Process

1. **Proposal** — Any engineer submits ADR with `PROPOSED` status
2. **Review** — ARB reviews within 5 business days
3. **Discussion** — GitHub Discussion for 10 business days
4. **Decision** — ARB votes (3/4 majority required)
5. **Ratification** — ADR marked `ACCEPTED`, Constitution version bumped
6. **Migration** — Implementation plan with timeline, rollback criteria

**Emergency amendments** (security, data loss): CTO + 1 ARB member can approve immediate hotfix with retroactive ratification within 30 days.

---

## Appendix A: Technology Stack (Ratified)

| Layer | Technology | Version | ADR |
|-------|------------|---------|-----|
| Monorepo | Turborepo + pnpm | 2.x / 9.x | ADR-001 |
| Backend | FastAPI | 0.115+ | ADR-002 |
| Frontend | Next.js 15 + React 19 | App Router, RSC | ADR-007 |
| Database | PostgreSQL 16 + pgvector | 16 / 0.7+ | ADR-005 |
| Cache/Queue | Redis 7 | 7.2+ | ADR-005 |
| Workflow | Temporal | 1.24+ | ADR-004 |
| AI Router | Custom (NVIDIA NIM primary) | — | ADR-006 |
| Auth | Supabase Auth v1 | — | ADR-008 |
| Event Bus | Redis Pub/Sub + LISTEN/NOTIFY | — | ADR-009 |
| Observability | OpenTelemetry, Prometheus, Grafana, Tempo | — | — |
| CI/CD | GitHub Actions | — | — |
| Container | Docker, Docker Compose, Kubernetes | — | — |

---

## Appendix B: Definition of Done (Per Feature)

A feature is **DONE** when:
- [ ] Linked GitHub Issue with acceptance criteria
- [ ] Technical design reviewed (ADR if architectural)
- [ ] Implementation complete with conventional commits
- [ ] Unit tests ≥80% coverage (domain/application)
- [ ] Integration tests for all adapters
- [ ] E2E test for critical path
- [ ] Security review passed (SAST, secrets, deps)
- [ ] Performance benchmark baseline recorded
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Documentation updated (API, DB, runbook, user guide)
- [ ] PR approved by 2 reviewers (1 domain owner)
- [ ] All CI gates green
- [ ] Deployed to staging, validated
- [ ] Changelog entry added
- [ ] Merged to `develop` (or `release/*`)

---

**End of Constitution**

*This document is the supreme engineering authority for ASTRA OS. All code, processes, and decisions must conform. Violations are technical debt by definition and must be remediated within the sprint they are discovered.*