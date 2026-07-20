# ASTRA OS — Deployment Guide

**Version**: 1.0
**Purpose**: Production deployment instructions for ASTRA OS

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Configuration](#configuration)
4. [Deployment Steps](#deployment-steps)
5. [Post-Deployment](#post-deployment)
6. [Rollback](#rollback)
7. [Monitoring](#monitoring)
8. [Security](#security)

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| `kubectl` | 1.28+ | Kubernetes CLI |
| `helm` | 3.12+ | Package manager (optional) |
| `kustomize` | 5.0+ | Kubernetes customization |
| `docker` | 24+ | Container builds |
| `aws-cli` / `gcloud` / `az` | Latest | Cloud provider CLI |
| `terraform` | 1.5+ | Infrastructure (optional) |

### Cloud Provider Accounts

- **AWS**: EKS, RDS, ElastiCache, S3, ALB, CloudWatch
- **GCP**: GKE, Cloud SQL, Memorystore, Cloud Storage, Cloud Load Balancing
- **Azure**: AKS, Azure Database for PostgreSQL, Azure Cache for Redis, Blob Storage, Application Gateway

---

## Infrastructure Requirements

### Kubernetes Cluster

| Component | Specification |
|-----------|---------------|
| **Kubernetes Version** | 1.28+ |
| **Node Pool - API** | 3-50 nodes, 2 vCPU / 4Gi RAM each |
| **Node Pool - Workers** | 2-20 nodes, 4 vCPU / 8Gi RAM each |
| **Node Pool - Frontend** | 2-10 nodes, 1 vCPU / 2Gi RAM each |
| **CNI** | Calico / Cilium / AWS VPC CNI |
| **CSI Driver** | EBS / GCE PD / Azure Disk |
| **Ingress Controller** | NGINX / AWS ALB / GCP Cloud Load Balancing |

### Managed Services

| Service | Specification |
|---------|---------------|
| **PostgreSQL** | 16+, Primary + 1 Replica, 4 vCPU / 16Gi RAM, 500GiB storage |
| **Redis** | 7+, Cluster Mode, 3 Shards, 2 vCPU / 4Gi RAM each |
| **Object Storage** | S3 / GCS / Azure Blob, Versioning enabled |
| **Container Registry** | ECR / GCR / ACR / GHCR |

### DNS & TLS

- **Domain**: `astra-os.com` (or your domain)
- **Wildcard Cert**: `*.astra-os.com` (Let's Encrypt / ACM / Cert-Manager)
- **DNS Records**:
  - `api.astra-os.com` → ALB/Load Balancer
  - `app.astra-os.com` → CloudFront/CDN
  - `*.astra-os.com` → Wildcard

---

## Configuration

### Environment Variables

Create `.env.production` in `apps/api/`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/astra
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://user:pass@host:6379/0
REDIS_CLUSTER=true

# Auth
JWT_SECRET_KEY=<64-char-random>
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=<service-key>

# Feature Flags
FEATURE_WORKFLOW_AUTOMATION=true
FEATURE_AI_CONTENT_GENERATION=true
FEATURE_SHADOW_MODE=true
FEATURE_SOCIAL_INTELLIGENCE=true

# Model Router
NVIDIA_NIM_API_KEY=<key>
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
GEMINI_API_KEY=<key>

# External APIs
META_APP_ID=<id>
META_APP_SECRET=<secret>
GOOGLE_ADS_DEVELOPER_TOKEN=<token>
GOOGLE_ADS_CLIENT_ID=<id>
GOOGLE_ADS_CLIENT_SECRET=<secret>
LINKEDIN_CLIENT_ID=<id>
LINKEDIN_CLIENT_SECRET=<secret>

# Storage
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=us-east-1
S3_BUCKET=astra-os-prod

# Observability
OTLP_ENDPOINT=https://otel-collector:4318/v1/traces
SENTRY_DSN=<dsn>
LOG_LEVEL=info

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<key>
FROM_EMAIL=noreply@astra-os.com

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=120
RATE_LIMIT_WHITELIST=/api/v1/health,/api/v1/metrics
```

### Frontend Environment

Create `.env.production` in `apps/web/`:

```bash
NEXT_PUBLIC_API_URL=https://api.astra-os.com/api/v1
NEXT_PUBLIC_WS_URL=wss://api.astra-os.com
NEXT_PUBLIC_APP_URL=https://app.astra-os.com
NEXT_PUBLIC_SENTRY_DSN=<dsn>
NEXT_PUBLIC_FEATURE_WORKFLOW_AUTOMATION=true
NEXT_PUBLIC_FEATURE_AI_CONTENT=true
NEXT_PUBLIC_FEATURE_SHADOW_MODE=true
NEXT_PUBLIC_FEATURE_SOCIAL_INTELLIGENCE=true
```

### Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace astra-prod

# Create secrets
kubectl create secret generic astra-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=JWT_SECRET_KEY="..." \
  --from-literal=OPENAI_API_KEY="..." \
  --from-literal=ANTHROPIC_API_KEY="..." \
  --from-literal=META_APP_SECRET="..." \
  --from-literal=SENTRY_DSN="..." \
  -n astra-prod

# TLS Secret (if using cert-manager)
kubectl create secret tls astra-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n astra-prod
```

---

## Deployment Steps

### 1. Build & Push Images

```bash
# Build API image
cd apps/api
docker build -t ghcr.io/webbixray/astra-api:v1.0.0 .
docker push ghcr.io/webbixray/astra-api:v1.0.0

# Build Frontend image
cd apps/web
docker build -t ghcr.io/webbixray/astra-web:v1.0.0 .
docker push ghcr.io/webbixray/astra-web:v1.0.0

# Build Worker image (if separate)
cd apps/api
docker build -f Dockerfile.worker -t ghcr.io/webbixray/astra-worker:v1.0.0 .
docker push ghcr.io/webbixray/astra-worker:v1.0.0
```

### 2. Apply Kubernetes Manifests

```bash
# Apply base manifests
kubectl apply -k k8s/overlays/prod

# Or step by step:
kubectl apply -k k8s/base
kubectl apply -k k8s/overlays/prod
```

### 3. Run Migrations

```bash
# Create migration job
kubectl apply -f k8s/jobs/migration.yaml

# Wait for completion
kubectl wait --for=condition=complete job/astra-migration -n astra-prod --timeout=300s

# Check logs
kubectl logs job/astra-migration -n astra-prod
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n astra-prod

# Check services
kubectl get svc -n astra-prod

# Check ingress
kubectl get ingress -n astra-prod

# Test health endpoint
curl https://api.astra-os.com/api/v1/health

# Test frontend
curl https://app.astra-os.com
```

---

## Post-Deployment

### 1. Seed Production Data

```bash
# Create admin user (if needed)
kubectl exec -it deployment/astra-api -n astra-prod -- \
  python -m scripts.create_admin --email admin@company.com --password "SecurePass123!"

# Create default organization
kubectl exec -it deployment/astra-api -n astra-prod -- \
  python -m scripts.create_org --name "Acme Corp" --slug "acme-corp"
```

### 2. Configure Monitoring

```bash
# Install Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Apply ServiceMonitors
kubectl apply -f k8s/monitoring/servicemonitors.yaml

# Apply Grafana Dashboards
kubectl apply -f k8s/monitoring/dashboards.yaml
```

### 3. Configure Alerting

```bash
# Apply Alertmanager config
kubectl apply -f k8s/monitoring/alertmanager.yaml

# Apply AlertRules
kubectl apply -f k8s/monitoring/alertrules.yaml
```

### 4. Verify End-to-End

```bash
# Test authentication
curl -X POST https://api.astra-os.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"SecurePass123!"}'

# Test campaign creation
curl -X POST https://api.astra-os.com/api/v1/campaigns \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Campaign","objective":"conversions","budget":1000}'

# Test workflow creation
curl -X POST https://api.astra-os.com/api/v1/workflows \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"organization_id":"<org-id>","name":"Test Workflow"}'
```

---

## Rollback

### Quick Rollback (Images)

```bash
# Rollback API
kubectl rollout undo deployment/astra-api -n astra-prod

# Rollback Frontend
kubectl rollout undo deployment/astra-web -n astra-prod

# Rollback Workers
kubectl rollout undo deployment/astra-worker -n astra-prod

# Check rollout status
kubectl rollout status deployment/astra-api -n astra-prod
```

### Full Rollback (Previous Version)

```bash
# Get previous revision
kubectl rollout history deployment/astra-api -n astra-prod

# Rollback to specific revision
kubectl rollout undo deployment/astra-api -n astra-prod --to-revision=3

# Verify
kubectl rollout status deployment/astra-api -n astra-prod
```

### Database Rollback (if migration applied)

```bash
# Check migration history
kubectl exec -it deployment/astra-api -n astra-prod -- alembic history

# Rollback one migration
kubectl exec -it deployment/astra-api -n astra-prod -- alembic downgrade -1

# Or specific revision
kubectl exec -it deployment/astra-api -n astra-prod -- alembic downgrade <revision>
```

---

## Monitoring

### Key Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **System Overview** | Grafana: `/d/system-overview` | RED metrics, capacity |
| **API Performance** | Grafana: `/d/api-performance` | Latency, throughput, errors |
| **Campaign ROI** | Grafana: `/d/campaign-roi` | ROAS, CPA, conversions |
| **Shadow Mode** | Grafana: `/d/shadow-mode` | Agreement rate, lift |
| **Cost Tracking** | Grafana: `/d/cost-tracking` | Daily spend, budgets |
| **SLA Compliance** | Grafana: `/d/sla-compliance` | Availability, latency, error budget |

### Critical Alerts

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| **API Down** | `up{job="astra-api"} == 0` | Critical | PagerDuty + Slack |
| **High Latency** | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1` | Warning | Slack |
| **High Error Rate** | `rate(http_requests_total{status=~"5.."}[5m]) > 0.05` | Critical | PagerDuty |
| **DB Connections** | `pg_stat_database_numbackends / pg_settings_max_connections > 0.8` | Warning | Slack |
| **Redis Memory** | `redis_memory_used_bytes / redis_memory_max_bytes > 0.85` | Warning | Slack |
| **Budget Warning** | `budget_utilization_pct > 80` | Warning | Email + Slack |
| **Budget Critical** | `budget_utilization_pct > 95` | Critical | PagerDuty |
| **SLA Breach** | `sla_compliance < target` | Critical | PagerDuty |
| **Shadow Mode Override** | `human_override_rate > 0.3` | Warning | Slack |

### Log Queries (Loki)

```logql
# API Errors
{job="astra-api"} |= "ERROR" | json | level="error"

# Slow Queries
{job="astra-api"} |= "slow_query" | json | duration_ms > 1000

# Agent Failures
{job="astra-api"} |= "agent_task_failed" | json

# Shadow Mode Conflicts
{job="astra-api"} |= "decision_conflict" | json
```

---

## Security

### Network Policies

```yaml
# Restrict API to internal + ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: astra-prod
spec:
  podSelector:
    matchLabels:
      app: astra-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - namespaceSelector:
        matchLabels:
          name: astra-prod
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: astra-prod
    - podSelector:
        matchLabels:
          app: postgres
    - podSelector:
        matchLabels:
          app: redis
```

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: astra-prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Secrets Management

- **Never** commit secrets to git
- Use **Sealed Secrets** or **External Secrets Operator**
- Rotate secrets quarterly
- Audit secret access monthly

### Compliance

- **SOC2 Type II**: Audit logs, access controls, encryption
- **GDPR**: Data deletion, consent management, DPA
- **CCPA**: Opt-out, data portability, deletion
- **HIPAA** (if applicable): BAA, encryption, audit logs

---

## Checklist

### Pre-Deployment
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Security scan passes (`trivy image ...`)
- [ ] Dependencies updated (`pip-audit`, `pnpm audit`)
- [ ] CHANGELOG.md updated
- [ ] Version bumped

### Deployment
- [ ] Images built and pushed
- [ ] Manifests applied
- [ ] Migrations run
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Monitoring alerts configured

### Post-Deployment
- [ ] Smoke tests in production
- [ ] Monitor dashboards for 30 min
- [ ] Verify critical user flows
- [ ] Update status page
- [ ] Notify stakeholders

---

## Support Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| **Platform Team** | platform@astra-os.com | Infrastructure issues |
| **Backend Team** | backend@astra-os.com | API issues |
| **Frontend Team** | frontend@astra-os.com | UI issues |
| **On-Call** | PagerDuty: astra-os-oncall | Critical incidents |
| **Security** | security@astra-os.com | Security incidents |

---

*This deployment guide should be reviewed and updated with each major release.*
