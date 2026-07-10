# Phase 1.8: Deployment Architecture

## Environment Strategy

| Environment | Purpose | Infrastructure |
|---|---|---|
| **Development** | Local development | Docker Compose (single machine) |
| **Staging** | Pre-production testing | Single-node K8s / Railway |
| **Production** | Live | Production K8s cluster (multi-node) |

## Development Environment (Docker Compose)

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Next.js  │  │ FastAPI  │  │ Temporal Server  │   │
│  │ :3000    │  │ :8000    │  │ :7233            │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│       │             │                                │
│       │             ▼                                │
│       │      ┌────────────┐  ┌────────────┐         │
│       │      │ PostgreSQL │  │   Redis    │         │
│       │      │ :5432      │  │ :6379      │         │
│       │      └────────────┘  └────────────┘         │
│       │                                             │
│       └──────────────────┬──────────────────────────│
│                          │                          │
│                          ▼                          │
│                   ┌──────────────┐                  │
│                   │ AI Router    │                  │
│                   │ (Ollama/NIM) │                  │
│                   └──────────────┘                  │
└─────────────────────────────────────────────────────┘
```

## Production Architecture (Kubernetes)

```
                         ┌─────────────┐
                         │  Cloud Load │
                         │  Balancer   │
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌─────────────┐         ┌─────────────┐
             │  Next.js     │         │  FastAPI     │
             │  (Deploy)    │         │  (Deploy)    │
             │  HPA: 2-10   │         │  HPA: 3-20   │
             └─────────────┘         └─────────────┘
                    │                       │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌─────────────┐         ┌─────────────┐
             │ PostgreSQL   │         │   Redis     │
             │ (HA via     │         │ (Sentinel   │
             │  Patroni)   │         │  or Cluster)│
             └─────────────┘         └─────────────┘

             ┌─────────────────────────────────────┐
             │         Services (Deployments)        │
             │                                       │
             │  ┌─────────────────────────────────┐  │
             │  │ Agent Orchestrator (HPA: 2-10)   │  │
             │  ├─────────────────────────────────┤  │
             │  │ Workflow Engine (Temporal Worker)│  │
             │  ├─────────────────────────────────┤  │
             │  │ Temporal Server (StatefulSet)    │  │
             │  ├─────────────────────────────────┤  │
             │  │ AI Router (HPA: 2-8)             │  │
             │  └─────────────────────────────────┘  │
             └─────────────────────────────────────┘

             ┌─────────────────────────────────────┐
             │         Background Workers            │
             │  ┌─────────────────────────────────┐  │
             │  │ Celery Worker (async tasks)      │  │
             │  ├─────────────────────────────────┤  │
             │  │ Analytics Aggregator             │  │
             │  ├─────────────────────────────────┤  │
             │  │ Email / Notification Sender      │  │
             │  └─────────────────────────────────┘  │
             └─────────────────────────────────────┘

             ┌─────────────────────────────────────┐
             │         Infrastructure               │
             │  ┌─────────────────────────────────┐  │
             │  │ Object Storage (S3/GCS)          │  │
             │  ├─────────────────────────────────┤  │
             │  │ NVIDIA NIM (GPU node pool)       │  │
             │  ├─────────────────────────────────┤  │
             │  │ Prometheus + Grafana             │  │
             │  ├─────────────────────────────────┤  │
             │  │ OpenTelemetry Collector          │  │
             │  └─────────────────────────────────┘  │
             └─────────────────────────────────────┘
```

## CI/CD Pipeline (GitHub Actions)

```
Push → main/staging
   │
   ▼
┌──────────────────┐
│ 1. Lint + Format  │
│ (ESLint, Ruff,    │
│  Prettier)        │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ 2. Type Check     │
│ (TypeScript,      │
│  mypy/Pyright)    │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ 3. Unit Tests     │
│ (Vitest, Pytest)  │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ 4. Build          │
│ (Next.js, Docker) │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ 5. Integration    │
│    Tests          │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ 6. Security Scan  │
│ (Trivy, Snyk)     │
└──────┬───────────┘
       ▼
┌──────────────────┐
│ 7. Deploy         │
│ (Staging / Prod)  │
└──────────────────┘
```

## Monitoring & Observability

| Tool | Purpose |
|---|---|
| **Prometheus** | Metrics collection |
| **Grafana** | Dashboards + alerting |
| **OpenTelemetry** | Distributed tracing |
| **Sentry** | Error tracking |
| **Loki** | Log aggregation |
| **PagerDuty** | Incident response |

### Key Metrics (SLOs)

| Metric | Target | Measurement |
|---|---|---|
| API Latency (p95) | <500ms | Prometheus histogram |
| AI Response (p95) | <3s | Prometheus histogram |
| Page Load (p95) | <1.5s | RUM data |
| Uptime | 99.9% | Prometheus + external probe |
| Error Rate | <0.1% | Sentry + logging |
| Workflow Execution | 99.5% success | Temporal metrics |

## GPU Strategy

- **Development**: Ollama (local CPU inference)
- **Staging**: NVIDIA NIM on single GPU (A10G)
- **Production**: NVIDIA NIM on GPU node pool (A100/H100)
- **Fallback**: Cloud API providers when GPU unavailable

## Networking

- **Ingress**: Nginx Ingress Controller + TLS termination
- **API Gateway**: Kong / Tyk (future Phase 3)
- **Service Mesh**: Linkerd (Phase 3, when service count > 10)
- **DNS**: Cloudflare / Route53
- **CDN**: Cloudflare / CloudFront (static assets)

## Secrets Management

- **HashiCorp Vault** (production)
- **GitHub Actions Secrets** (CI/CD)
- **Kubernetes Secrets** (encrypted at rest)
- **No secrets in code, env files, or Docker images**
