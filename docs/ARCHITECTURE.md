# ASTRA OS — Architecture Documentation

**Version**: 1.0
**Last Updated**: 2024

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Clean Architecture Layers](#clean-architecture-layers)
4. [Domain Model](#domain-model)
5. [Service Communication](#service-communication)
6. [Data Flow](#data-flow)
7. [Technology Stack](#technology-stack)
8. [Deployment Architecture](#deployment-architecture)
9. [Security Architecture](#security-architecture)
10. [Observability Architecture](#observability-architecture)

---

## System Overview

ASTRA OS is an **AI-Native Marketing & Business Growth Operating System** that provides:

- **Agent Orchestration**: Hierarchical AI agents (CEO → Directors → Specialists)
- **Campaign Management**: Full lifecycle from creation to optimization
- **Workflow Engine**: Visual builder with templates, versioning, and replay
- **Social Intelligence**: Comment monitoring, AI auto-reply, moderation
- **Shadow Mode**: Agent/human decision comparison with lift measurement
- **Observability**: Metrics, alerting, cost tracking, SLA monitoring, dashboards

---

## Architecture Principles

### 1. Clean Architecture (ADR-002)
- **Domain** is the center - no external dependencies
- **Application** orchestrates use cases
- **Infrastructure** implements ports/adapters
- **Presentation** handles HTTP, serialization, auth

### 2. Domain-Driven Design (DDD)
- Aggregates, Entities, Value Objects
- Domain Events for cross-aggregate communication
- Repository pattern for persistence abstraction

### 3. Event-Driven Architecture
- Domain Event Bus for async communication
- Redis Pub/Sub for distributed deployments
- Event sourcing for audit trails

### 4. Multi-Tenancy
- Organization-scoped data isolation
- Row-Level Security (RLS) policies
- Feature flags per organization

### 5. AI-First Design
- Model Router with fallback chain
- Agent hierarchy with governance
- RAG integration for grounded responses

---

## Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  FastAPI Routes │ Middleware │ Serialization │ Auth         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  Use Cases │ DTOs │ Event Handlers │ Service Orchestration  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  Entities │ Aggregates │ Value Objects │ Domain Events      │
│  Domain Services │ Repository Interfaces │ Domain Policies   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
│  SQLAlchemy Models │ Repository Implementations │ Adapters  │
│  Event Bus (Redis) │ Model Router │ External APIs           │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Examples |
|-------|---------------|----------|
| **Presentation** | HTTP handling, serialization, auth, validation | FastAPI routes, Pydantic models, middleware |
| **Application** | Use case orchestration, DTOs, cross-cutting concerns | Use cases, DTOs, event handlers, service wiring |
| **Domain** | Business logic, rules, invariants | Entities, value objects, domain services, events |
| **Infrastructure** | External concerns, persistence, external APIs | SQLAlchemy repos, Redis event bus, HTTP clients |

---

## Domain Model

### Core Aggregates

```
Organization
├── Users (TeamMembers)
├── Campaigns
│   ├── AdAccounts
│   ├── Creatives
│   ├── Budgets
│   └── ABTests
├── Workflows
│   ├── WorkflowExecutions
│   └── WorkflowTemplates
├── Content
│   ├── BrandVoices
│   └── ContentTemplates
├── Workflows (AI)
│   ├── WorkflowVersions
│   └── WorkflowExecutions
├── Knowledge
│   ├── KnowledgeNodes
│   ├── Memories
│   └── KnowledgeRelations
├── Social Intelligence
│   ├── SocialComments
│   ├── AutoReplies
│   └── ReplyTemplates
├── Shadow Mode
│   ├── ShadowSessions
│   ├── ShadowDecisions
│   └── LiftMeasurements
└── Observability
    ├── MetricDefinitions
    ├── AlertRules
    ├── Alerts
    ├── CostRecords
    ├── Budgets
    ├── SLADefinitions
    ├── SLAReports
    ├── Dashboards
    └── DashboardWidgets
```

### Key Domain Concepts

| Concept | Description |
|---------|-------------|
| **Organization** | Tenant boundary, all data scoped to org |
| **Campaign** | Marketing campaign with budget, targeting, creatives |
| **Workflow** | Visual DAG of nodes/edges for automation |
| **Agent** | AI specialist with autonomy level & governance |
| **Shadow Session** | Agent/human decision comparison environment |
| **Shadow Decision** | Single decision point with agent+human comparison |

---

## Service Communication

### Synchronous (Request/Response)
- FastAPI routes → Use Cases → Domain Services
- Internal service calls via dependency injection

### Asynchronous (Event-Driven)
```
Domain Event → Event Bus (Redis Pub/Sub) → Event Handlers
```

**Event Types**:
- `campaign.created` / `campaign.launched` / `campaign.completed`
- `workflow.created` / `workflow.executed` / `workflow.completed`
- `agent.task_completed` / `agent.task_failed`
- `shadow.decision_made` / `shadow.decision_compared` / `shadow.lift_measured`
- `alert.fired` / `alert.resolved`
- `budget.warning` / `budget.critical`

### Agent Communication (ADR-003)
- **Redis Message Bus** for A2A communication
- **AgentAuditTrail** for full reasoning trace
- **GovernanceMiddleware** enforces autonomy levels at runtime

---

## Data Flow

### Campaign Creation Flow
```
POST /campaigns
    │
    ▼
CampaignRoutes.create_campaign()
    │
    ▼
CreateCampaignUseCase.execute()
    │
    ▼
Campaign.create()  [Domain Entity]
    │
    ▼
CampaignRepository.save()  [Infrastructure]
    │
    ▼
DomainEvent: campaign.created → EventBus
    │
    ▼
Event Handlers (async):
  - AuditLogHandler
  - NotificationHandler
  - AnalyticsHandler
```

### Shadow Mode Decision Flow
```
Agent makes decision
    │
    ▼
ShadowDecisionService.record_agent_decision()
    │
    ▼
Auto-approve if confidence ≥ threshold
    │
    ▼
Human reviews (if needed)
    │
    ▼
POST /decisions/{id}/human
    │
    ▼
ShadowDecisionService.record_human_decision()
    │
    ▼
Auto-compare → ComparisonResult
    │
    ▼
Outcome recorded → LiftMeasurement
```

### Auto-Reply Generation Flow
```
Comment webhook
    │
    ▼
SocialComment received → CommentAnalyzer.analyze()
    │
    ▼
AutoReplyGenerator.generate_reply()
    │
    ▼
Confidence scoring → Auto-approve if ≥ 0.85
    │
    ▼
If pending: Human reviews → Approve/Reject
    │
    ▼
POST /replies/{id}/send → Platform API
```

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | FastAPI | 0.109+ |
| **Language** | Python | 3.12+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Async DB** | asyncpg | 0.29+ |
| **Database** | PostgreSQL | 16 |
| **Cache/PubSub** | Redis | 7 |
| **Message Bus** | Redis Pub/Sub | - |
| **Migrations** | Alembic | 1.13+ |
| **Validation** | Pydantic | 2.5+ |
| **Auth** | PyJWT / Supabase | - |
| **Testing** | pytest / pytest-asyncio | 7.4+ |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | Next.js | 15 (App Router) |
| **Language** | TypeScript | 5.3+ |
| **UI Library** | React | 19 |
| **Styling** | Tailwind CSS | 4 |
| **Components** | shadcn/ui | latest |
| **State** | TanStack Query | 5 |
| **Forms** | React Hook Form + Zod | - |

### Infrastructure
| Component | Technology |
|-----------|------------|
| **Containerization** | Docker (multi-stage) |
| **Orchestration** | Kubernetes (Kustomize) |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus + Grafana |
| **Logging** | Loki |
| **Tracing** | Tempo |
| **Secrets** | Sealed Secrets / Vault |

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL CLIENTS                          │
│   Web App │ Mobile App │ Third-party Integrations │ Webhooks    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API GATEWAY / LOAD BALANCER                  │
│              (nginx / AWS ALB / Cloudflare)                      │
│              TLS Termination │ Rate Limiting │ WAF               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                            │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   API PODS      │  │  WORKER PODS    │  │  FRONTEND PODS  │  │
│  │  (FastAPI)      │  │  (Celery/Async) │  │  (Next.js)      │  │
│  │  HPA: 3-50      │  │  HPA: 2-20      │  │  HPA: 2-10      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  POSTGRESQL     │  │  REDIS CLUSTER  │  │  OBJECT STORE   │  │
│  │  (Primary/Replica)│  │  (Sentinel)     │  │  (S3/MinIO)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              OBSERVABILITY STACK                             ││
│  │  Prometheus │ Grafana │ Loki │ Tempo │ Alertmanager         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Kubernetes Resources

| Component | Replicas | Resources | HPA |
|-----------|----------|-----------|-----|
| **API** | 3-50 | 500m CPU / 1Gi RAM | CPU > 70% |
| **Workers** | 2-20 | 1 CPU / 2Gi RAM | Queue depth > 100 |
| **Frontend** | 2-10 | 100m CPU / 256Mi RAM | CPU > 80% |
| **PostgreSQL** | 1 Primary + 1 Replica | 4 CPU / 16Gi RAM | - |
| **Redis** | 3 Sentinel + 3 Replicas | 2 CPU / 4Gi RAM | - |

---

## Security Architecture

### Authentication & Authorization
- **JWT** with RS256 signing (Supabase)
- **Short-lived access tokens** (15 min) + **refresh tokens** (7 days)
- **RBAC**: org roles (owner, admin, member, viewer)
- **Feature flags** per organization

### Data Protection
- **Encryption at rest**: PostgreSQL TDE + S3 SSE-KMS
- **Encryption in transit**: TLS 1.3 everywhere
- **Secrets**: HashiCorp Vault / Sealed Secrets
- **PII**: Field-level encryption for sensitive data

### Network Security
- **Zero-trust**: mTLS between services (Istio/Linkerd)
- **Egress control**: Egress gateway for external APIs
- **WAF**: Cloudflare / AWS WAF at edge

### Governance (ADR-003)
- **Autonomy Levels**: 0 (Advisory) → 1 (Semi-auto) → 2 (Full-auto)
- **GovernanceMiddleware**: Runtime enforcement per agent/org
- **Audit Trail**: Immutable log for all agent actions

---

## Observability Architecture

### Four Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                      METRICS (Prometheus)                    │
│  RED Metrics │ USE Metrics │ Business Metrics │ Custom      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        LOGS (Loki)                           │
│  Structured JSON │ Correlation IDs │ Log Levels │ Labels     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       TRACES (Tempo)                         │
│  Distributed Tracing │ Span Attributes │ Service Graph       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ALERTING (Alertmanager)                 │
│  Multi-channel │ Routing │ Inhibition │ Silences             │
└─────────────────────────────────────────────────────────────┘
```

### Key Dashboards

| Dashboard | Purpose |
|-----------|---------|
| **System Overview** | RED metrics, system health, capacity |
| **API Performance** | Latency, throughput, error rates by endpoint |
| **Agent Performance** | Task success rate, token usage, latency |
| **Campaign ROI** | ROAS, CPA, conversion rates by campaign |
| **Shadow Mode** | Agreement rate, lift, human override rate |
| **Cost Tracking** | Daily spend, budget utilization, projections |
| **SLA Compliance** | Availability, latency, error budget burn |

---

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Monorepo with Turborepo | Accepted |
| ADR-002 | Clean Architecture | Accepted |
| ADR-003 | Custom Agent Orchestrator | Accepted |
| ADR-004 | PostgreSQL + pgvector | Accepted |
| ADR-005 | Redis for Pub/Sub & Cache | Accepted |
| ADR-006 | Model Router (NVIDIA NIM → OpenAI → Anthropic → Gemini) | Accepted |
| ADR-007 | Next.js 15 + App Router | Accepted |
| ADR-008 | Supabase Auth + Custom RBAC | Accepted |

---

## Glossary

| Term | Definition |
|------|------------|
| **Organization** | Tenant/business entity, top-level data boundary |
| **Campaign** | Marketing campaign with objective, budget, targeting |
| **Workflow** | Visual DAG of nodes/edges for process automation |
| **Agent** | AI specialist with defined role, autonomy level, tools |
| **Shadow Mode** | Agent runs alongside human for decision comparison |
| **Lift** | Percentage improvement of agent vs human/baseline |
| **RAG** | Retrieval-Augmented Generation for grounded AI |
| **Governance** | Runtime enforcement of autonomy & policies |
| **Budget Pacing** | Daily spend distribution to avoid overspend |
| **ROAS** | Return on Ad Spend (revenue / ad spend) |

---

## Appendix: Directory Structure

```
astra-os/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── domain/         # Domain layer
│   │   │   ├── application/    # Application layer
│   │   │   ├── infrastructure/ # Infrastructure layer
│   │   │   └── presentation/   # Presentation layer
│   │   └── tests/              # Backend tests
│   └── web/                    # Next.js frontend
│       ├── src/
│       │   ├── app/            # App Router pages
│       │   ├── features/       # Feature modules
│       │   ├── components/     # Shared components
│       │   └── lib/            # Utilities, API client
│       └── tests/              # Frontend tests
├── services/                   # Shared services (agent orchestrator)
├── packages/                   # Shared packages
├── docker/                     # Dockerfiles
├── k8s/                        # Kubernetes manifests
├── scripts/                    # Utility scripts
└── docs/                       # Documentation
```

---

*This architecture document is a living document. Update with each major architectural decision.*
