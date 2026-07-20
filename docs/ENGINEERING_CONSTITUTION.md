# ASTRA OS — Engineering Constitution

**Version**: 1.0
**Status**: Binding
**Authority**: CTO + Engineering Leads
**Review**: Quarterly

---

## Preamble

This Constitution establishes the immutable engineering standards for ASTRA OS. All code, architecture decisions, and processes must comply. Exceptions require written approval from CTO + 2 Engineering Leads.

---

## Article I: Architecture Standards

### 1.1 Clean Architecture (ADR-002)
- **Domain Layer**: Pure Python, zero external dependencies
- **Application Layer**: Use cases, DTOs, orchestration
- **Infrastructure Layer**: SQLAlchemy, Redis, HTTP clients, external APIs
- **Presentation Layer**: FastAPI routes, Pydantic schemas, middleware

**Rule**: Domain never imports from Infrastructure or Presentation.

### 1.2 Domain-Driven Design
- Aggregates enforce invariants
- Entities have identity, Value Objects are immutable
- Domain Events for cross-aggregate communication
- Repository interfaces in Domain, implementations in Infrastructure

### 1.3 Event-Driven Architecture (ADR-005)
- Domain Events published to Redis Pub/Sub
- Event Handlers in Application layer
- Async processing for non-critical paths
- Event sourcing for audit trails (Shadow Mode, Audit Logs)

### 1.4 Multi-Tenancy
- All data scoped to `organization_id`
- Row-Level Security (RLS) policies on all tables
- Feature flags per organization
- No cross-org queries allowed

---

## Article II: Code Standards

### 2.1 Python (Backend)

#### Style
- **Formatter**: Ruff (line-length=100)
- **Linter**: Ruff (all rules + pydantic, fastapi, sqlalchemy)
- **Type Checker**: MyPy (strict mode)
- **Imports**: Absolute, grouped (stdlib, third-party, local)

#### Patterns
- **Async First**: All I/O async, sync only for CPU-bound
- **Type Hints**: Required on all public functions
- **Dataclasses**: Use `@dataclass` for entities, `slots=True` when possible
- **Exceptions**: Custom domain exceptions, never bare `Exception`

#### Prohibited
- Global mutable state
- Circular imports
- `Any` type without justification
- `**kwargs` in public APIs
- Bare `except:`
- Mutating function arguments

### 2.2 TypeScript (Frontend)

#### Style
- **Formatter**: Prettier (single quotes, trailing commas)
- **Linter**: ESLint (Airbnb + TypeScript)
- **Strict Mode**: Enabled
- **Explicit Types**: No `any`, use `unknown` if needed

#### Patterns
- **React**: Functional components, hooks, Server Components by default
- **State**: TanStack Query for server state, Zustand for client state
- **Forms**: React Hook Form + Zod validation
- **Components**: shadcn/ui primitives, composition over inheritance

#### Prohibited
- Class components
- `useEffect` for data fetching (use TanStack Query)
- Inline styles (use Tailwind)
- `any` type
- Direct DOM manipulation

### 2.3 Database (PostgreSQL)

#### Conventions
- **Tables**: snake_case, plural (`campaigns`, `workflow_executions`)
- **Columns**: snake_case, descriptive (`created_at`, not `c_at`)
- **Primary Keys**: UUID (`uuid_generate_v4()`)
- **Foreign Keys**: Explicit, indexed, `ON DELETE CASCADE` where appropriate
- **Enums**: Native PostgreSQL enums, not CHECK constraints
- **JSONB**: For flexible schemas (nodes, edges, config)
- **Indexes**: Composite for query patterns, partial for filters

#### Migrations
- **Tool**: Alembic
- **Naming**: `YYYYMMDD_HHMMSS_description.py`
- **Reversible**: Every migration must have `downgrade()`
- **Data Migrations**: Separate from schema migrations
- **Review Required**: All migrations reviewed by 2 engineers

---

## Article III: AI & Agent Standards

### 3.1 Model Router (ADR-006)
- **Primary**: NVIDIA NIM (local/GPU)
- **Fallback Chain**: OpenAI → Anthropic → Gemini
- **Cost Tracking**: Per-request, per-organization
- **Rate Limits**: Per-provider, per-organization
- **Fallback Logic**: Automatic on error/timeout

### 3.2 Agent Hierarchy (ADR-003)
```
CEOAgent (Level 2 autonomy)
├── MarketingDirector → [ContentSpecialist, SEOSpecialist, SocialSpecialist]
├── CreativeDirector → [Copywriter, Designer, BrandVoice]
├── AdvertisingDirector → [CampaignOptimizer, BidManager, AudienceResearcher]
├── ResearchDirector → [MarketResearcher, CompetitorAnalyst, TrendAnalyzer]
├── AnalyticsDirector → [DataAnalyst, AttributionModeler, ReportGenerator]
├── WorkflowDirector → [WorkflowBuilder, AutomationScheduler, IntegrationManager]
└── ComplianceDirector → [ContentReviewer, PrivacyAuditor, PolicyEnforcer]
```

### 3.3 Agent Runtime
- **Base Class**: `ReActAgent` (Reasoning + Acting loop)
- **Tools**: Registered via decorator, typed schemas
- **Memory**: Working (in-context), Episodic (PostgreSQL), Semantic (pgvector)
- **Governance**: Middleware enforces autonomy level at runtime
- **Audit Trail**: Every action logged with reasoning trace

### 3.4 Governance (M3)
- **Autonomy Levels**: 0=Advisory, 1=Semi-auto, 2=Full-auto
- **Approval Rules**: Spend >$100, new audiences, brand-sensitive content
- **Explainability**: Every decision traceable to reasoning + context
- **Audit Log**: Immutable, queryable, exportable (GDPR/CCPA)

---

## Article IV: Testing Standards

### 4.1 Coverage Requirements
| Layer | Minimum | Target |
|-------|---------|--------|
| Domain | 95% | 100% |
| Application | 90% | 95% |
| Infrastructure | 80% | 90% |
| Presentation | 70% | 80% |
| **Overall** | **85%** | **90%** |

### 4.2 Test Types
| Type | Scope | Speed | Location |
|------|-------|-------|----------|
| Unit | Single function/class | <10ms | `tests/unit/` |
| Integration | Multiple layers | <1s | `tests/integration/` |
| Contract | API contracts | <5s | `tests/contract/` |
| E2E | Full user flows | <30s | `tests/e2e/` (Playwright) |

### 4.3 Test Patterns
- **AAA Pattern**: Arrange, Act, Assert
- **Fixtures**: Shared in `conftest.py`, scoped appropriately
- **Mocks**: Only for external dependencies, use `AsyncMock` for async
- **Data**: Factory functions, not fixtures for complex objects
- **Deterministic**: No random, no time-dependent, no external calls

### 4.4 Property-Based Testing
- Use Hypothesis for complex domain logic
- Required for: parsers, serializers, validators, algorithms

---

## Article V: Security Standards

### 5.1 Authentication & Authorization
- **JWT**: RS256, 15min access, 7d refresh, rotation
- **RBAC**: Org roles (owner, admin, member, viewer)
- **Feature Flags**: Per-org, per-user override
- **Session Management**: Redis-backed, secure cookies

### 5.2 Data Protection
- **Encryption at Rest**: PostgreSQL TDE + S3 SSE-KMS
- **Encryption in Transit**: TLS 1.3 everywhere
- **Field-Level Encryption**: PII, secrets, API keys
- **Key Management**: HashiCorp Vault / AWS KMS

### 5.3 Application Security
- **Input Validation**: Pydantic on all inputs
- **Output Encoding**: Auto-escaping in templates
- **Rate Limiting**: Per-endpoint, per-organization
- **CORS**: Restrictive, configurable per org
- **CSP**: Strict, nonce-based
- **Dependencies**: `pip-audit` / `pnpm audit` weekly

### 5.4 Compliance
- **SOC2 Type II**: Audit logs, access controls, retention
- **GDPR**: Right to deletion, portability, consent
- **CCPA**: Opt-out, disclosure, non-discrimination
- **Audit Trail**: All mutations logged with actor, timestamp, diff

---

## Article V: Observability Standards

### 5.1 Four Pillars
| Pillar | Tool | Standard |
|--------|------|----------|
| **Metrics** | Prometheus | RED (Rate, Errors, Duration) + USE (Utilization, Saturation, Errors) |
| **Logs** | Loki | Structured JSON, correlation IDs, structured levels |
| **Traces** | Tempo | 100% sampling for errors, 10% for success |
| **Alerts** | Alertmanager | Multi-channel, routing, inhibition, silences |

### 5.2 Key Metrics (RED)
| Metric | Target | Alert |
|--------|--------|-------|
| **Request Rate** | >1000/s | N/A |
| **Error Rate** | <0.1% | >0.5% |
| **Latency p99** | <500ms | >1s |
| **Availability** | 99.9% | <99.5% |

### 5.3 Logging Standards
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "trace_id": "abc123",
  "span_id": "def456",
  "service": "astra-api",
  "message": "Campaign launched",
  "organization_id": "uuid",
  "user_id": "uuid",
  "duration_ms": 45,
  "metadata": {}
}
```

### 5.3 Alerting Rules
- **No alert fatigue**: <5 alerts/day/engineer
- **Actionable**: Every alert has runbook
- **Tiered**: Critical (page), Warning (slack), Info (log)
- **Deduplication**: Group by fingerprint
- **Silences**: Planned maintenance windows

---

## Article VI: Deployment Standards

### 6.1 CI/CD Pipeline
```
Push → Lint → TypeCheck → UnitTests → IntegrationTests → Build → SecurityScan → Deploy Staging → E2E Tests → Deploy Production
```

### 6.2 Environments
| Env | Purpose | Auto-Deploy | Approval |
|-----|---------|-------------|----------|
| **Dev** | Development | On push to develop | None |
| **Staging** | Integration testing | On PR merge | Auto |
| **Production** | Live traffic | On tag | Manual (2 approvals) |

### 6.3 Deployment Strategies
- **API**: Rolling (maxSurge=25%, maxUnavailable=0)
- **Workers**: Rolling with drain
- **Frontend**: Blue-Green (CloudFront invalidation)
- **Database**: Expand/Contract (backward compatible)

### 6.4 Rollback
- **Automatic**: Health check failure → auto-rollback
- **Manual**: `kubectl rollout undo` (≤30s)
- **Database**: `alembic downgrade` (tested in staging)

---

## Article VI: Review & Evolution

### 6.1 Amendment Process
1. Propose via RFC (GitHub Discussion)
2. Discussion period: 1 week minimum
3. Approval: CTO + 2 Engineering Leads
4. Document in ADR, update Constitution
5. Communicate to all engineers

### 6.2 Compliance
- **Automated**: CI enforces formatting, linting, types, tests
- **Manual**: Architecture reviews for new services
- **Audit**: Quarterly Constitution compliance audit
- **Exceptions**: Documented in ADR with expiry date

### 6.3 Versioning
- **Constitution Version**: Semantic (MAJOR.MINOR.PATCH)
- **MAJOR**: Breaking architectural change
- **MINOR**: New standard, backward compatible
- **PATCH**: Clarification, typo fix

---

## Appendix: ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Monorepo with Turborepo | Accepted |
| ADR-002 | Clean Architecture | Accepted |
| ADR-003 | Custom Agent Orchestrator | Accepted |
| ADR-004 | PostgreSQL + pgvector | Accepted |
| ADR-005 | Redis Pub/Sub for Events | Accepted |
| ADR-006 | Model Router (NVIDIA NIM → OpenAI → Anthropic → Gemini) | Accepted |
| ADR-007 | Next.js 15 + App Router | Accepted |
| ADR-008 | Supabase Auth + Custom RBAC | Accepted |

---

## Ratification

**Signed**: _________________________
**CTO**: _________________________
**Date**: _________________________

**Engineering Leads**: _________________________
**Date**: _________________________

---

*This Constitution is a living document. All engineers are expected to know and follow it. Ignorance is not a valid defense for non-compliance.*
