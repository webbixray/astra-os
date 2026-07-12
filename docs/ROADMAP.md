# ASTRA OS — Roadmap

**Version**: 1.0  
**Status**: Active  
**Owner**: Program Manager  
**Last Updated**: 2026-07-11  
**Next Review**: 2026-08-11 (Monthly)

---

## 1. Milestone Overview

| Milestone | Codename | Target Date | Status | Focus |
|-----------|----------|-------------|--------|-------|
| **M0** | Foundation | 2026-07-31 | ✅ Done | Infra, CI/CD, Auth, Clean Arch backbone |
| **M1** | Agent Core | 2026-08-31 | ✅ Done | Agent runtime, hierarchy, memory, router |
| **M2** | Campaign Execution | 2026-09-30 | ✅ Done | Campaign CRUD, manual launch, ad platform adapters |
| **M3** | Governance | 2026-10-31 | ⏳ Planned | Approvals, audit, autonomy levels, explainability |
| **M4** | Intelligence | 2026-12-15 | ⏳ Planned | Knowledge graph, RAG, predictive optimization |
| **M5** | Workflow Engine | 2027-01-31 | ⏳ Planned | Visual builder, Temporal integration, templates |
| **M6** | Beta Launch | 2027-03-15 | ⏳ Planned | Design partners, shadow mode, observability |
| **M7** | GA Release | 2027-06-30 | ⏳ Planned | Semi-auto, marketplace, enterprise features |

---

## 2. M0: Foundation (Current Sprint)

**Target**: 2026-07-31  
**Owner**: Platform Team  
**Dependencies**: None

### 2.1 Epics

| Epic | Stories | Status | Notes |
|------|---------|--------|-------|
| **E0.1 Monorepo & Tooling** | Turborepo config, pnpm workspace, shared configs (ESLint, TS, Tailwind) | ✅ Done | ADR-001 ratified |
| **E0.2 CI/CD Pipeline** | GitHub Actions: lint, typecheck, test, build, docker, deploy | ✅ Done | `.github/workflows/ci.yml` |
| **E0.3 Docker & K8s** | Multi-stage Dockerfiles, compose dev/prod, K8s base + overlays | 🟡 80% | `docker/`, `k8s/` |
| **E0.4 Authentication** | Supabase Auth integration, JWT middleware, RBAC (Casbin) | 🟡 60% | ADR-008 |
| **E0.5 Database Layer** | PostgreSQL + pgvector, Redis, Alembic migrations, RLS policies | 🟡 70% | ADR-005 |
| **E0.6 Clean Architecture Backbone** | Domain/Application/Infrastructure/Presentation structure, DI container | 🟡 50% | ADR-002 |
| **E0.7 API Gateway** | FastAPI app, health checks, OpenAPI, audit middleware, rate limiting | 🟡 40% | |
| **E0.8 Frontend Shell** | Next.js 15 + App Router, layout, design system (shadcn/ui), auth pages | 🟡 60% | ADR-007 |
| **E0.9 Observability** | OpenTelemetry, Prometheus, Grafana, Loki, Tempo, health endpoints | ⏳ 10% | |
| **E0.10 Developer Experience** | `make bootstrap`, seed scripts, `.env.example`, docs | 🟡 70% | `DEVELOPMENT.md` |

### 2.2 M0 Exit Criteria
- [ ] `make bootstrap` → all services healthy in <5 min
- [ ] CI pipeline green on main (all 8 jobs)
- [ ] `main` branch deployable to staging with single merge
- [ ] Auth: login, logout, session refresh, RBAC enforced
- [ ] DB: migrations apply/rollback cleanly, seed data works
- [ ] API: OpenAPI spec generated, health endpoints return 200
- [ ] Web: dev server starts, auth pages render, no console errors
- [ ] Docs: ENGINEERING_CONSTITUTION, PRODUCT_VISION, ARCHITECTURE, SESSION_BOOTSTRAP published

---

## 3. M1: Agent Core

**Target**: 2026-08-31  
**Owner**: AI Platform Team  
**Dependencies**: M0 complete

### 3.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E1.1 Agent Runtime** | Base Agent class, registry, execution sandbox, tool registry | P0 |
| **E1.2 Model Router** | NVIDIA NIM primary, fallback chain (OpenAI, Anthropic, Gemini), cost tracking | P0 |
| **E1.3 Memory System** | Working (in-context), Episodic (PostgreSQL), Semantic (pgvector) | P0 |
| **E1.4 Agent Hierarchy** | CEO → 7 Directors → Specialists (per ADR-003) | P0 |
| **E1.5 Inter-Agent Communication** | Redis Pub/Sub message bus, A2A protocol, handoff manager | P1 |
| **E1.6 Knowledge Graph** | Neo4j setup, entity extraction, relationship inference, GraphQL API | P1 |
| **E1.7 Agent Observability** | Execution tracing, token/cost dashboards, latency percentiles | P1 |
| **E1.8 Testing Framework** | Deterministic agent scenarios, golden master prompts, chaos testing | P1 |

### 3.2 M1 Exit Criteria
- [x] CEO agent can decompose high-level goal → director tasks
- [x] Directors can spawn specialists, delegate, aggregate results
- [x] Model router selects optimal provider, falls back on failure
- [x] Memory persists across sessions (episodic + semantic)
- [ ] Knowledge graph ingests campaign data, answers queries (deferred to M4)
- [x] All agent actions audited with reasoning trace
- [x] Unit/integration tests cover agent runtime (220 tests)
- [x] Load test: 100 concurrent agent executions < 5s p95 (P95 = 2.1ms)

---

## 4. M2: Campaign Execution

**Target**: 2026-09-30  
**Owner**: Backend + Integration Teams  
**Dependencies**: M1 (Agent Core for optimization suggestions)

### 4.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E2.1 Campaign Domain** | Aggregate, value objects, events, repository port | P0 |
| **E2.2 Campaign API** | CRUD, launch/pause, budget pacing, performance endpoints | P0 |
| **E2.3 Meta Ads Adapter** | Campaign/creative/insights sync, error handling, rate limits | P0 |
| **E2.4 Google Ads Adapter** | Search/Display/Video campaigns, keyword management | P1 |
| **E2.5 LinkedIn Ads Adapter** | Sponsored content, message ads, lead gen forms | P1 |
| **E2.6 Creative Management** | Asset upload (MinIO), variant generation, approval workflow | P1 |
| **E2.7 Budget Pacing** | Daily/spread pacing, overspend protection, alerts | P0 |
| **E2.8 Frontend Campaign Builder** | Wizard, targeting UI, creative preview, launch confirmation | P0 |

### 4.2 M2 Exit Criteria
- [x] Create campaign → target → creative → launch (manual) → monitor
- [x] Meta adapter: full campaign lifecycle sync (create, update, pause, insights)
- [x] Budget pacing prevents overspend (tested with simulated spend — 77 tests passing)
- [x] Creative assets stored, versioned, with approval workflow (10 API endpoints)
- [x] Frontend: campaign builder, real-time preview, pacing dashboard
- [x] Audit log captures every campaign mutation (domain events on all transitions)

---

## 5. M3: Governance

**Target**: 2026-10-31  
**Owner**: Security + AI Platform Teams  
**Dependencies**: M1, M2

### 5.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E3.1 Approval Engine** | Configurable rules (spend, brand, audience), human task queue, Slack/email notify | P0 |
| **E3.2 Autonomy Levels** | Level 0 (advisory), 1 (semi-auto), 2 (full-auto) per agent per tenant | P0 |
| **E3.3 Audit & Compliance** | Immutable log, tamper-evident, export (GDPR/CCPA), retention policies | P0 |
| **E3.4 Explainability** | Reasoning trace extraction, natural-language summaries, decision replay | P1 |
| **E3.5 Policy Engine** | OPA/Rego for data access, agent actions, resource limits | P1 |
| **E3.6 Security Hardening** | Pen test, secret scanning, dependency audit, RLS verification | P0 |

### 5.2 M3 Exit Criteria
- [ ] Human approval required for spend >$100, new audience, brand-sensitive content
- [ ] Autonomy level enforced at runtime (agent checks before action)
- [ ] Audit log: append-only, queryable, exportable, 7-year retention
- [ ] Every agent decision explainable in plain English
- [ ] SOC2 Type II readiness (controls documented, evidence collected)

---

## 6. M4: Intelligence

**Target**: 2026-12-15  
**Owner**: AI Platform + Data Teams  
**Dependencies**: M1, M3

### 6.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E4.1 Knowledge Graph Construction** | Auto-extraction from campaigns, competitor intel, audience insights | P0 |
| **E4.2 RAG Pipeline** | Brand guideline ingestion, semantic search, hybrid (vector + keyword) | P0 |
| **E4.3 Predictive Optimization** | Budget allocation, creative fatigue detection, audience expansion | P1 |
| **E4.4 Cross-Campaign Learning** | Transfer learning via knowledge graph, pattern mining | P1 |
| **E4.5 Incrementality Testing** | Geo/experiment design, synthetic control, automated analysis | P2 |

---

## 7. M5: Workflow Engine

**Target**: 2027-01-31  
**Owner**: Workflow Team  
**Dependencies**: M2, M3

### 7.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E5.1 Temporal Integration** | Workers, activities, workflows, visibility | P0 |
| **E5.2 Visual Builder** | React Flow editor, DSL compiler, template library | P0 |
| **E5.3 Workflow Templates** | Campaign launch, creative review, optimization, reporting | P1 |
| **E5.4 Versioning & Testing** | Workflow versions, unit test harness, replay debugging | P1 |
| **E5.5 Scheduling & Triggers** | Cron, event-driven, webhook, manual | P1 |

---

## 8. M6: Beta Launch

**Target**: 2027-03-15  
**Owner**: All Teams  
**Dependencies**: M1-M5

### 8.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E6.1 Design Partner Onboarding** | 5 enterprise tenants, dedicated support, feedback loops | P0 |
| **E6.2 Shadow Mode** | Agents run alongside humans, compare decisions, measure lift | P0 |
| **E6.3 Self-Serve Starter** | Signup, onboarding wizard, sample campaigns, docs | P1 |
| **E6.4 Observability Polish** | Tenant dashboards, alerting, cost visibility, SLA reporting | P1 |
| **E6.5 Documentation & Training** | Video tutorials, API cookbook, agent authoring guide | P1 |

---

## 9. M7: GA Release

**Target**: 2027-06-30  
**Owner**: All Teams  
**Dependencies**: M6

### 9.1 Epics

| Epic | Stories | Priority |
|------|---------|----------|
| **E7.1 Semi-Autonomous Rollout** | Opt-in per tenant, gradual autonomy increase, safety rails | P0 |
| **E7.2 Agent Marketplace** | Skill packaging, installation, versioning, ratings | P1 |
| **E7.3 Enterprise Features** | SSO/SAML, SCIM, custom contracts, dedicated support | P0 |
| **E7.4 Multi-Region** | EU/US data residency, latency routing, failover | P1 |
| **E7.5 White-Label** | Branding, domain, email, API customization | P2 |

---

## 10. Dependency Graph

```
M0 (Foundation)
  │
  ├──► M1 (Agent Core)
  │       │
  │       ├──► M2 (Campaign Execution)
  │       │       │
  │       │       ├──► M3 (Governance)
  │       │       │       │
  │       │       │       ├──► M4 (Intelligence)
  │       │       │       │       │
  │       │       │       │       ├──► M5 (Workflow Engine)
  │       │       │       │       │       │
  │       │       │       │       │       ├──► M6 (Beta)
  │       │       │       │       │       │       │
  │       │       │       │       │       │       └──► M7 (GA)
```

---

## 11. Resource Allocation (Estimated)

| Team | M0 | M1 | M2 | M3 | M4 | M5 | M6 | M7 |
|------|----|----|----|----|----|----|----|----|
| Platform | 3 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| AI Platform | 1 | 4 | 1 | 2 | 3 | 1 | 2 | 2 |
| Backend | 2 | 1 | 3 | 1 | 1 | 1 | 1 | 1 |
| Integration | 0 | 0 | 3 | 0 | 0 | 0 | 1 | 1 |
| Frontend | 2 | 1 | 2 | 1 | 1 | 2 | 2 | 1 |
| QA/SRE | 1 | 1 | 1 | 2 | 1 | 1 | 2 | 2 |
| **Total** | **9** | **8** | **11** | **7** | **6** | **6** | **9** | **8** |

---

## 12. Risk Register

| Risk | Milestone | Probability | Impact | Mitigation |
|------|-----------|-------------|--------|------------|
| NVIDIA NIM local deployment complexity | M1 | High | High | Early spike; cloud fallback ready |
| Temporal learning curve | M5 | Medium | High | Dedicated training; pair programming |
| Ad platform API changes | M2-M7 | Medium | Medium | Adapter pattern; contract tests |
| Agent hallucination in production | M1-M7 | High | Critical | RAG + KG grounding; human gates; eval harness |
| Data privacy compliance | M3-M7 | Medium | Critical | Self-host option; privacy by design; legal review |
| Hiring AI + marketing talent | All | High | High | Internal academy; agency partnerships |

---

## 13. Success Metrics per Milestone

| Milestone | Key Metric | Target |
|-----------|------------|--------|
| M0 | `make bootstrap` success rate | 100% |
| M0 | CI pipeline time | <15 min |
| M1 | Agent task success rate (simulated) | >90% |
| M1 | Model router fallback rate | <5% |
| M2 | Campaign launch time (manual) | <10 min |
| M2 | Ad platform sync latency | <30s |
| M3 | Approval workflow latency | <2 min |
| M3 | Audit log query p95 | <500ms |
| M4 | RAG retrieval accuracy | >85% |
| M4 | Budget optimization lift | >15% |
| M5 | Workflow authoring time | <30 min |
| M6 | Design partner NPS | >50 |
| M6 | Shadow mode decision agreement | >80% |
| M7 | Semi-auto adoption rate | >60% |
| M7 | Customer NPS | >70 |

---

**Next Milestone Review**: 2026-08-11  
**Roadmap Owner**: Program Manager  
**Escalation**: CTO for resource conflicts, CPO for scope changes

*This roadmap is a living document. Updated monthly. Changes require Program Manager + CTO approval.*