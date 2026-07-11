# ASTRA OS — Technical Architecture

**Version**: 1.0  
**Status**: Ratified  
**Owner**: Chief Architect  
**Last Updated**: 2026-07-11  
**ADR References**: ADR-001 through ADR-009 (see `docs/adr/ADR-INDEX.md`)

---

## 1. System Context (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ASTRA OS SYSTEM                                  │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │   Marketing  │    │   Platform   │    │   External   │    │  Identity │  │
│  │   Operators  │◄──►│   (Web/App)  │◄──►│   Ad Platforms│    │  Provider │  │
│  │  (Humans)    │    │              │    │  (Meta, Google│    │ (Supabase)│  │
│  └──────────────┘    └──────┬───────┘    │  LinkedIn...) │    └───────────┘  │
│                             │            └──────────────┘                    │
│                             ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API GATEWAY (FastAPI)                          │   │
│  │  Auth │ Rate Limit │ Routing │ OpenAPI │ WebSocket │ Audit Log     │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                             │
│        ┌──────────────────────┼──────────────────────┐                     │
│        ▼                      ▼                      ▼                     │
│ ┌─────────────┐        ┌─────────────┐        ┌─────────────┐             │
│ │  Campaign   │        │   Agent     │        │  Workflow   │             │
│ │  Service    │◄──────►│ Orchestrator│◄──────►│  Engine     │             │
│ │             │        │             │        │  (Temporal) │             │
│ └──────┬──────┘        └──────┬──────┘        └──────┬──────┘             │
│        │                      │                      │                     │
│        ▼                      ▼                      ▼                     │
│ ┌─────────────────────────────────────────────────────────────────────┐   │
│ │                    SHARED INFRASTRUCTURE LAYER                        │   │
│ │  PostgreSQL+pgvector │ Redis │ MinIO │ NVIDIA NIM │ Neo4j │ Temporal │   │
│ └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Container Diagram (C4 Level 2)

### 2.1 Backend Services

| Container | Technology | Responsibility | Ports |
|-----------|------------|----------------|-------|
| **API Gateway** | FastAPI + Uvicorn | Auth, routing, rate limiting, OpenAPI, audit | 8000 |
| **Campaign Service** | FastAPI | Campaign CRUD, budget pacing, scheduling | 8001 |
| **Agent Orchestrator** | Python (custom) | Agent lifecycle, hierarchy, memory, tool exec | 8002 |
| **Workflow Engine** | Temporal Python SDK | Durable execution, retries, saga patterns | 7233 (gRPC) |
| **AI Router** | Python (custom) | Model selection, fallback, cost tracking | 8003 |
| **Knowledge Graph** | Python + Neo4j | Entity extraction, relationship inference | 8004 |
| **Notification Service** | FastAPI | Email, Slack, webhook delivery | 8005 |

### 2.2 Frontend

| Container | Technology | Responsibility |
|-----------|------------|----------------|
| **Web App** | Next.js 15 + React 19 | Dashboard, campaign builder, agent monitor, settings |
| **Storybook** | Storybook 8 | UI component documentation |

### 2.3 Infrastructure

| Container | Technology | Purpose |
|-----------|------------|---------|
| **PostgreSQL 16** | Primary DB + pgvector | Relational data, embeddings, outbox |
| **Redis 7** | Cache, Pub/Sub, Streams | Session, rate limit, event bus, queue |
| **Temporal** | Workflow durability | Long-running workflows, retries, visibility |
| **MinIO** | S3-compatible | Asset storage, model artifacts, exports |
| **NVIDIA NIM** | Local LLM inference | Primary model serving (Llama 3.1, Nemotron) |
| **Neo4j** | Graph database | Knowledge graph, entity relationships |
| **Supabase Auth** | Auth service | AuthN/AuthZ, OAuth, MFA, SSO |

---

## 3. Component Diagram (C4 Level 3) — Backend

### 3.1 API Gateway (`apps/api/app/gateway/`)
```
gateway/
├── middleware/
│   ├── auth.py           # JWT validation, Supabase sync
│   ├── rate_limit.py     # Token bucket per tenant/user
│   ├── audit.py          # Request/response logging to audit table
│   └── correlation.py    # X-Request-ID propagation
├── routes/
│   ├── health.py         # /health, /ready (k8s probes)
│   ├── campaigns.py      # Proxy to Campaign Service
│   ├── agents.py         # Proxy to Agent Orchestrator
│   └── workflows.py      # Proxy to Workflow Engine
└── openapi.py            # Custom OpenAPI generation
```

### 3.2 Campaign Service (`services/campaigns/`) — Clean Architecture
```
campaigns/
├── domain/
│   ├── entities/
│   │   ├── campaign.py           # Aggregate root
│   │   ├── campaign_status.py    # Enum: DRAFT → REVIEW → ACTIVE → PAUSED → COMPLETED
│   │   └── budget.py             # Value object with pacing logic
│   ├── value_objects/
│   │   ├── date_range.py
│   │   ├── targeting_spec.py
│   │   └── creative_asset.py
│   ├── events/
│   │   ├── campaign_created.py
│   │   ├── campaign_launched.py
│   │   └── budget_exhausted.py
│   └── repositories/             # Port interfaces
│       └── campaign_repository.py
├── application/
│   ├── use_cases/
│   │   ├── create_campaign.py
│   │   ├── launch_campaign.py
│   │   ├── pause_campaign.py
│   │   ├── update_budget.py
│   │   └── get_performance.py
│   ├── dto/
│   │   ├── campaign_dto.py
│   │   └── performance_dto.py
│   └── services/
│       └── budget_pacing_service.py
├── infrastructure/
│   ├── db/
│   │   ├── models/
│   │   │   └── campaign_model.py     # SQLAlchemy
│   │   └── repositories/
│   │       └── sql_campaign_repository.py
│   ├── api/
│   │   ├── meta_client.py
│   │   ├── google_ads_client.py
│   │   └── linkedin_client.py
│   └── events/
│       └── outbox_publisher.py       # Transactional outbox
├── presentation/
│   ├── routes.py          # FastAPI router
│   └── schemas.py         # Pydantic request/response
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

### 3.3 Agent Orchestrator (`services/agent-orchestrator/`)
```
agent_orchestrator/
├── runtime/
│   ├── agent.py              # Base Agent class
│   ├── agent_registry.py     # Registration, discovery, health
│   ├── execution_context.py  # Sandbox, timeouts, resource limits
│   └── tool_registry.py      # Tool definitions, validation, execution
├── hierarchy/
│   ├── ceo_agent.py          # Strategic planning, delegation
│   ├── director_agents/      # Marketing, Creative, Ads, Research, Analytics, Workflow, Compliance
│   └── specialist_agents/    # Content, SEO, Social, Copywriter, Designer, etc.
├── memory/
│   ├── working_memory.py     # In-context, per-session
│   ├── episodic_memory.py    # PostgreSQL: execution traces, decisions
│   ├── semantic_memory.py    # pgvector: embeddings, brand guidelines
│   └── knowledge_graph.py    # Neo4j: entities, relationships, queries
├── router/
│   ├── model_router.py       # NVIDIA NIM → OpenAI → Anthropic → Gemini
│   ├── cost_tracker.py       # Per-agent, per-tenant token accounting
│   └── fallback_chain.py     # Circuit breaker, latency-based routing
├── governance/
│   ├── approval_engine.py    # Human-in-the-loop workflows
│   ├── audit_logger.py       # Immutable action log
│   ├── autonomy_policy.py    # Level 0/1/2 per agent per tenant
│   └── explainability.py     # Reasoning trace extraction
└── communication/
    ├── message_bus.py        # Redis Pub/Sub for inter-agent
    ├── protocol.py           # A2A message schema (JSON-RPC style)
    └── handoff_manager.py    # Context transfer between agents
```

### 3.4 Workflow Engine (`services/workflow-engine/`)
```
workflow_engine/
├── temporal/
│   ├── activities/           # Temporal activities (deterministic, retryable)
│   │   ├── campaign_activities.py
│   │   ├── agent_activities.py
│   │   └── integration_activities.py
│   ├── workflows/            # Temporal workflows (durable, replayable)
│   │   ├── campaign_execution_workflow.py
│   │   ├── creative_review_workflow.py
│   │   └── optimization_workflow.py
│   └── worker.py             # Worker process configuration
├── builder/
│   ├── visual_editor.py      # React Flow → Temporal DSL
│   ├── dsl/
│   │   ├── schema.json       # Workflow definition schema
│   │   └── compiler.py       # Visual → Temporal code
│   └── templates/            # Pre-built workflow templates
└── monitoring/
    ├── visibility.py         # Temporal UI integration
    └── metrics.py            # Custom metrics export
```

### 3.5 AI Router (`services/ai-router/`)
```
ai_router/
├── providers/
│   ├── base.py               # Abstract provider interface
│   ├── nvidia_nim.py         # Primary: Llama 3.1, Nemotron 3 Ultra
│   ├── openai.py             # Fallback: GPT-4o, o1
│   ├── anthropic.py          # Fallback: Claude 3.5 Sonnet
│   └── gemini.py             # Fallback: Gemini 1.5 Pro
├── routing/
│   ├── strategy.py           # Cost/latency/quality optimization
│   ├── fallback.py           # Circuit breaker, health checks
│   └── load_balancer.py      # Request distribution
├── optimization/
│   ├── prompt_cache.py       # Semantic caching (pgvector)
│   ├── token_counter.py      # Accurate counting per model
│   └── cost_estimator.py     # Pre-flight cost estimation
└── observability/
    ├── usage_tracker.py      # Per-tenant, per-agent, per-model
    └── latency_monitor.py    # p50/p95/p99 per provider
```

---

## 4. Data Architecture

### 4.1 PostgreSQL Schema (Core Tables)

```sql
-- Tenants & Users
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'starter',
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    supabase_user_id UUID UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- owner, admin, operator, viewer
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    objective VARCHAR(100),
    budget_cents BIGINT NOT NULL,
    spent_cents BIGINT NOT NULL DEFAULT 0,
    daily_budget_cents BIGINT,
    start_date DATE,
    end_date DATE,
    targeting JSONB NOT NULL DEFAULT '{}',
    creative_assets JSONB NOT NULL DEFAULT '[]',
    settings JSONB NOT NULL DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    launched_at TIMESTAMPTZ
);

-- Agent System
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    type VARCHAR(100) NOT NULL,  -- CEO, MARKETING_DIRECTOR, CONTENT_SPECIALIST, etc.
    name VARCHAR(255) NOT NULL,
    autonomy_level SMALLINT NOT NULL DEFAULT 0,  -- 0=advisory, 1=semi-auto, 2=full-auto
    parent_agent_id UUID REFERENCES agents(id),
    configuration JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    campaign_id UUID REFERENCES campaigns(id),
    input JSONB NOT NULL,
    reasoning TEXT,
    tool_calls JSONB NOT NULL DEFAULT '[]',
    output JSONB,
    status VARCHAR(50) NOT NULL,  -- PENDING, RUNNING, COMPLETED, FAILED, APPROVAL_REQUIRED
    human_approval_id UUID,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    tokens_used INT NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0
);

-- Audit Log (Append-only, partitioned by month)
CREATE TABLE audit_logs (
    id BIGSERIAL,
    tenant_id UUID NOT NULL,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    before JSONB,
    after JSONB,
    metadata JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, created_at, id)
) PARTITION BY RANGE (created_at);

-- Outbox Pattern for Reliable Events
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX idx_outbox_unpublished ON outbox (created_at) WHERE published_at IS NULL;
```

### 4.2 pgvector Embeddings
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    source_type VARCHAR(50) NOT NULL,  -- campaign, brand_guideline, creative, competitor
    source_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- text-embedding-3-large dimension
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX embeddings_tenant_source ON embeddings (tenant_id, source_type, source_id);
CREATE INDEX embeddings_vector ON embeddings USING hnsw (embedding vector_cosine_ops);
```

### 4.3 Redis Data Structures
| Key Pattern | Type | TTL | Purpose |
|-------------|------|-----|---------|
| `session:{tenant_id}:{user_id}` | String (JSON) | 24h | User session |
| `rate_limit:{tenant_id}:{endpoint}` | String (counter) | 1m | Rate limiting |
| `agent:memory:{agent_id}:working` | Hash | 1h | Working memory |
| `events:{tenant_id}:{event_type}` | Stream | 7d | Event sourcing |
| `cache:embeddings:{hash}` | String | 30d | Embedding cache |
| `queue:campaign_tasks` | List | — | Background jobs |
| `pubsub:agent:{tenant_id}` | Pub/Sub | — | Inter-agent messaging |

### 4.4 Neo4j Knowledge Graph Schema
```cypher
// Node Labels
(:Brand {id, tenant_id, name, voice_attributes, guidelines_url})
(:Campaign {id, tenant_id, name, objective, status, budget})
(:Audience {id, tenant_id, name, demographics, interests, behaviors})
(:Creative {id, tenant_id, campaign_id, type, content, performance_metrics})
(:Competitor {id, tenant_id, name, website, strengths, weaknesses})
(:Channel {id, name, platform})  // Meta, Google, LinkedIn, etc.
(:Metric {id, campaign_id, date, spend, impressions, clicks, conversions})

// Relationships
(:Brand)-[:OWNS]->(:Campaign)
(:Campaign)-[:TARGETS]->(:Audience)
(:Campaign)-[:USES]->(:Creative)
(:Campaign)-[:RUNS_ON]->(:Channel)
(:Campaign)-[:HAS_METRIC]->(:Metric)
(:Brand)-[:COMPETES_WITH]->(:Competitor)
(:Creative)-[:GENERATED_BY]->(:Agent)
(:Agent)-[:REPORTS_TO]->(:Agent)  // Hierarchy
```

---

## 5. API Design (OpenAPI 3.1)

### 5.1 REST Conventions
- **Base Path**: `/api/v1`
- **Versioning**: URL path (`/api/v1/`, `/api/v2/`)
- **Authentication**: Bearer JWT (Supabase)
- **Tenant Isolation**: `X-Tenant-ID` header or subdomain
- **Pagination**: Cursor-based (`?cursor=&limit=20`)
- **Filtering**: `?filter[field]=value`
- **Sorting**: `?sort=-created_at,name`

### 5.2 Core Endpoints

| Resource | Endpoints |
|----------|-----------|
| **Campaigns** | `GET/POST /campaigns`, `GET/PATCH/DELETE /campaigns/{id}`, `POST /campaigns/{id}/launch`, `POST /campaigns/{id}/pause`, `GET /campaigns/{id}/performance` |
| **Agents** | `GET/POST /agents`, `GET/PATCH /agents/{id}`, `POST /agents/{id}/execute`, `GET /agents/{id}/executions`, `GET /agents/{id}/memory` |
| **Workflows** | `GET/POST /workflows`, `GET/PATCH/DELETE /workflows/{id}`, `POST /workflows/{id}/execute`, `GET /workflows/{id}/runs` |
| **Knowledge** | `POST /knowledge/ingest`, `GET /knowledge/search`, `GET /knowledge/graph` |
| **Integrations** | `GET/POST /integrations`, `POST /integrations/{id}/test`, `GET /integrations/{id}/accounts` |
| **Audit** | `GET /audit/logs` (filtered, paginated) |
| **Billing** | `GET /billing/usage`, `GET /billing/invoices` |

### 5.3 WebSocket Events
- `ws://api/ws/agents/{agent_id}` — Real-time agent execution stream
- `ws://api/ws/campaigns/{campaign_id}` — Campaign status updates
- `ws://api/ws/workflows/{run_id}` — Workflow execution progress

---

## 6. Security Architecture

### 6.1 Authentication & Authorization
```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────►│  API Gateway │────►│  Supabase Auth  │
│  (Web/App)  │     │  (FastAPI)   │     │   (JWT/JWKS)    │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐
                    │  RBAC Check  │
                    │  (Casbin)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Tenant      │
                    │  Isolation   │
                    │  (Row Level  │
                    │   Security)  │
                    └──────────────┘
```

### 6.2 RBAC Model (Casbin)
```ini
# Policy: role, resource, action
p, owner, campaigns, *
p, admin, campaigns, read, write, launch
p, operator, campaigns, read, write
p, viewer, campaigns, read

p, owner, agents, *
p, admin, agents, read, execute, configure
p, operator, agents, read, execute

# Tenant isolation enforced at DB level via RLS
```

### 6.3 Data Protection
- **Encryption at Rest**: AES-256 (managed by cloud provider)
- **Encryption in Transit**: TLS 1.3 everywhere
- **Secrets**: HashiCorp Vault (production) / Doppler (dev)
- **PII Handling**: Field-level encryption for email, phone, IP
- **Data Retention**: Configurable per tenant (default 7 years audit, 90 days metrics)

### 6.4 AI Safety
- **Prompt Injection**: Input sanitization, instruction hierarchy
- **Output Validation**: Schema validation, regex guards
- **Tool Safety**: Allowlist, parameter validation, timeout, resource limits
- **Audit Trail**: Every agent action logged with reasoning

---

## 7. Observability

### 7.1 Four Pillars

| Pillar | Implementation | Key Metrics |
|--------|----------------|-------------|
| **Metrics** | Prometheus + Grafana | Request rate, latency (p50/p95/p99), error rate, queue depth, agent execution time, token usage, cost |
| **Logs** | Structured JSON → Loki | Request logs, agent reasoning traces, audit events, errors with stack traces |
| **Traces** | OpenTelemetry → Tempo | End-to-end request flow, agent handoffs, tool calls, DB queries, external API calls |
| **Profiles** | Pyroscope | CPU/memory hotspots in agent runtime, workflow workers |

### 7.2 Critical Dashboards
1. **System Health** — API latency, error rate, saturation, throughput
2. **Agent Fleet** — Executions/min, success rate, avg tokens, cost/hr, autonomy level distribution
3. **Campaign Performance** — Spend, ROAS, CPA by channel, creative fatigue
4. **Workflow Engine** — Running/completed/failed, duration, retry rate
5. **AI Router** — Provider health, latency, cost, fallback rate
6. **Tenant Usage** — Active users, campaigns, agents, storage, API calls

### 7.3 Alerting (PagerDuty)
| Alert | Condition | Severity |
|-------|-----------|----------|
| API Error Rate | >1% for 5m | P1 |
| Agent Execution Failure | >5% for 10m | P1 |
| Workflow Stuck | >30m no progress | P2 |
| Database Connections | >80% pool | P2 |
| Redis Memory | >85% | P2 |
| Cost Spike | >2x daily avg | P3 |
| Model Provider Down | Health check fail | P1 |

---

## 8. Deployment Architecture

### 8.1 Environments
| Env | Purpose | Infra | Data |
|-----|---------|-------|------|
| **Local** | Development | Docker Compose | Synthetic/seed |
| **Preview** | PR validation | K8s (ephemeral) | Scrubbed production subset |
| **Staging** | Integration testing | K8s (dedicated) | Anonymized production copy |
| **Production** | Customer traffic | K8s (multi-AZ) | Live |

### 8.2 Kubernetes (Helm + Kustomize)
```
k8s/
├── base/
│   ├── namespace.yaml
│   ├── network-policies.yaml
│   ├── rbac.yaml
│   ├── secrets.yaml (ExternalSecrets)
│   ├── configmap.yaml
│   ├── deployment-api.yaml
│   ├── deployment-web.yaml
│   ├── deployment-workers.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── servicemonitor.yaml
├── overlays/
│   ├── local/
│   ├── preview/
│   ├── staging/
│   └── production/
```

### 8.3 Resource Quotas (Production)
| Component | Replicas | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|----------|-------------|----------------|-----------|--------------|
| API Gateway | 3-10 (HPA) | 500m | 512Mi | 2000m | 2Gi |
| Campaign Service | 2-8 | 250m | 256Mi | 1000m | 1Gi |
| Agent Orchestrator | 2-6 | 1000m | 2Gi | 4000m | 8Gi |
| Workflow Workers | 3-20 | 500m | 1Gi | 2000m | 4Gi |
| AI Router | 2-6 | 500m | 1Gi | 2000m | 4Gi |
| Web (Next.js) | 3-10 | 250m | 256Mi | 1000m | 1Gi |

---

## 9. Integration Architecture

### 9.1 Ad Platform Adapters (Hexagonal)
```
adapters/
├── meta/
│   ├── client.py           # Graph API wrapper
│   ├── campaign_mapper.py  # Domain ↔ Meta Campaign
│   ├── creative_mapper.py
│   └── insights_mapper.py
├── google_ads/
│   ├── client.py           # Google Ads API wrapper
│   ├── campaign_mapper.py
│   └── ...
├── linkedin/
├── tiktok/
└── base.py                 # AbstractAdPlatform interface
```

### 9.2 Event Contracts (Shared Types)
```python
# packages/shared/events/campaign.py
class CampaignLaunched(BaseModel):
    event_type: Literal["campaign.launched"] = "campaign.launched"
    tenant_id: UUID
    campaign_id: UUID
    timestamp: datetime
    payload: CampaignLaunchedPayload

class CampaignLaunchedPayload(BaseModel):
    name: str
    budget_cents: int
    channels: List[str]
    targeting: TargetingSpec
```

---

## 10. Development Standards

### 10.1 Code Organization (Enforced by Constitution)
```
# Backend feature module
feature_name/
├── domain/           # Pure Python, zero deps
├── application/      # Use cases, DTOs, ports
├── infrastructure/   # Adapters (DB, API, MQ)
├── presentation/     # FastAPI routes, Pydantic schemas
└── tests/            # Unit, integration, fixtures

# Frontend feature module
feature_name/
├── components/       # React components
├── hooks/            # Custom hooks (React Query, Zustand)
├── api/              # API client (generated from OpenAPI)
├── stores/           # State management
├── types/            # TypeScript interfaces
└── tests/            # Unit, component, E2E
```

### 10.2 Code Quality Gates (CI)
| Check | Tool | Threshold |
|-------|------|-----------|
| Format | ruff format / prettier | Zero diff |
| Lint | ruff / eslint | Zero errors |
| Types | mypy / tsc --noEmit | Zero errors |
| Security | bandit / semgrep / trivy | No HIGH/CRITICAL |
| Dependencies | safety / npm audit | No critical vulns |
| Unit Coverage | pytest-cov / vitest | ≥80% lines, ≥70% branches |
| Integration | pytest + testcontainers | All critical paths |
| E2E | playwright | All critical journeys |
| Performance | k6 | p95 < 200ms (API), < 3s (Web) |
| Accessibility | axe-core | WCAG 2.1 AA |

### 10.3 Database Migrations
- **Tool**: Alembic (auto-generate + manual review)
- **Naming**: `YYYYMMDD_HHMMSS_description.py`
- **Rules**: 
  - No destructive changes without rollback plan
  - Backward-compatible first (add column, then migrate data, then drop)
  - Linear history enforced (no merge heads)
  - Tested in CI with `alembic downgrade -1 && upgrade head`

---

## 11. Disaster Recovery

### 11.1 RTO/RPO Targets
| Tier | RTO | RPO | Strategy |
|------|-----|-----|----------|
| **Database** | 15 min | 1 min | PITR + streaming replica |
| **Redis** | 5 min | 0 (best effort) | AOF + replica |
| **Object Storage** | 1 hr | 1 hr | Cross-region replication |
| **Kubernetes** | 30 min | 0 | GitOps (ArgoCD) + etcd backup |
| **Secrets** | 5 min | 0 | Vault replication |

### 11.2 Backup Schedule
- **PostgreSQL**: Continuous WAL archiving + daily base backup (retained 30 days)
- **Neo4j**: Daily full backup + incremental (retained 14 days)
- **Temporal**: Built-in visibility + history retention (90 days)
- **Kubernetes**: Velero daily (cluster resources) + hourly (PVs)

---

## 12. Architecture Decision Log

See `docs/adr/ADR-INDEX.md` for ratified decisions:
- ADR-001: Monorepo (Turborepo + pnpm)
- ADR-002: Clean Architecture (Feature-first)
- ADR-003: Custom Agent Orchestrator
- ADR-004: Workflow Engine (Temporal)
- ADR-005: Database (PostgreSQL + pgvector, Redis)
- ADR-006: AI Model Router (NVIDIA NIM primary)
- ADR-007: Frontend (Next.js 15 + App Router)
- ADR-008: Authentication (Supabase Auth)
- ADR-009: Event-Driven (Redis Pub/Sub + LISTEN/NOTIFY)

---

**End of Architecture Document**

*This document is the technical source of truth. All implementation must conform. Deviations require ADR.*