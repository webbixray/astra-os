# Astra OS - Production Hardening Action Plan

**Generated:** 2025-07-16
**Status:** In Progress
**Based on:** Static analysis of codebase, Docker, K8s, CI/CD, and security configs

---

## Executive Summary

The Astra OS codebase has **excellent foundations** for production readiness with:
- ✅ Multi-stage Dockerfiles (distroless runtime)
- ✅ Comprehensive K8s manifests with Kustomize overlays
- ✅ Kyverno security policies (Pod Security Standards Restricted)
- ✅ Network policies (default deny)
- ✅ GitHub Actions CI/CD with security scanning (Bandit, Semgrep, Trivy, TruffleHog, pip-audit)
- ✅ SBOM generation (Syft) and image signing (Cosign)
- ✅ Comprehensive test suite (unit, integration, observability)
- ✅ Health/readiness/liveness probes
- ✅ Structured logging, OpenTelemetry, Prometheus metrics
- ✅ Circuit breakers, DLQ, rate limiting

**Gaps identified:** See Critical Actions below.

---

## Critical Actions (Do First - Block Production)

### 1. Fix Production Docker Compose - **IN PROGRESS**
- [x] Update `docker/prod/docker-compose.yml` to use production Dockerfiles
- [x] Create `apps/web/Dockerfile` for production
- [ ] Verify `docker/prod/docker-compose.yml` uses correct context paths
- [ ] Test production build: `docker compose -f docker/prod/docker-compose.yml build`

### 2. Create `.env.production.template` with Required Variables
```bash
# Required for production
POSTGRES_PASSWORD=<64-char-random>
REDIS_PASSWORD=<64-char-random>
SECRET_KEY=<64-char-random>
DOMAIN=app.astra.com
SENTRY_DSN=https://xxx@sentry.io/xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GEMINI_API_KEY=xxx

# Optional
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

### 3. Add SSL Certificates for Production Nginx
```bash
# Generate self-signed for testing (replace with Let's Encrypt in prod)
mkdir -p docker/prod/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/prod/ssl/key.pem \
  -out docker/prod/ssl/cert.pem \
  -subj "/CN=app.astra.com"
```

### 4. Verify K8s Secrets Management
- [ ] Replace `secretGenerator` literals with External Secrets Operator
- [ ] Add `external-secrets.yaml` for each secret source (Vault, AWS Secrets Manager, etc.)
- [ ] Remove hardcoded `SECRET_KEY=change-me-in-production` from kustomization

### 5. Run Security Scans Locally Before Push
```bash
# Python
cd apps/api && pip-audit --desc && bandit -r app/ && trufflehog git file://. --only-verified

# Node
cd apps/web && npm audit && npx trufflehog filesystem . --only-verified

# Container
trivy image astra-api:latest && trivy image astra-web:latest
hadolint apps/api/Dockerfile && hadolint apps/web/Dockerfile
```

---

## High Priority Actions (Complete Before Launch)

### 6. Dependency Hardening
- [ ] Pin all dependencies to exact versions (no `^` or `~` in production)
- [ ] Enable `pip-audit` in CI to fail on HIGH/CRITICAL
- [ ] Enable `npm audit` with `--audit-level=high` in CI
- [ ] Add `renovate.json` or Dependabot config for automated updates

### 7. Container Hardening Verification
- [ ] Verify distroless base image: `gcr.io/distroless/python3-debian12:nonroot`
- [ ] Confirm non-root user (UID 65532) in runtime
- [ ] Verify read-only root filesystem in K8s (Kyverno policy exists)
- [ ] Drop ALL capabilities (Kyverno policy exists)
- [ ] Add `securityContext` to all K8s deployments:
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 65532
    runAsGroup: 65532
    fsGroup: 65532
    readOnlyRootFilesystem: true
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
  ```

### 8. API Security Hardening
- [ ] Verify CSP header in `config.py` is production-ready
- [ ] Ensure CORS origins are explicit (no `*`)
- [ ] Verify rate limiting: 30 req/s API, 5 req/m auth
- [ ] Add request size limits (nginx: `client_max_body_size 50M`)
- [ ] Verify JWT tokens use RS256 (not HS256) with key rotation

### 9. Database Security
- [ ] Enable PostgreSQL SSL (`sslmode=require`)
- [ ] Use PgBouncer for connection pooling
- [ ] Enable row-level security (RLS) for multi-tenancy
- [ ] Automate backup encryption and cross-region replication

### 10. Redis Security
- [ ] Require AUTH (already in prod compose)
- [ ] Enable TLS for Redis
- [ ] Disable dangerous commands (FLUSHDB, CONFIG, etc.)

---

## Medium Priority Actions (Post-Launch Sprint)

### 11. Observability Completeness
- [ ] Deploy Prometheus + Grafana stack (kube-prometheus-stack)
- [ ] Deploy Loki + Tempo for logs/traces
- [ ] Configure OTel Collector with batch processor
- [ ] Create SLO dashboards with burn-rate alerts
- [ ] Add custom business metrics (agent runs, content generated, API costs)

### 12. Chaos Engineering
- [ ] Install LitmusChaos or Chaos Mesh
- [ ] Run 10 baseline experiments (pod kill, latency, CPU, memory, DNS, network partition)
- [ ] Document blast radius and recovery procedures

### 13. Disaster Recovery
- [ ] Test PostgreSQL PITR restore monthly
- [ ] Test Velero backup/restore for K8s resources
- [ ] Document RPO/RTO targets (RPO ≤ 1hr, RTO ≤ 4hr)
- [ ] Run quarterly DR drill

### 14. Compliance Automation
- [ ] Implement `astra compliance export --framework SOC2`
- [ ] Automate evidence collection for auditors
- [ ] Add data retention/deletion cron jobs

---

## Low Priority Actions (Continuous Improvement)

### 15. Supply Chain Security (SLSA Level 3)
- [ ] Provenance attestations for all builds
- [ ] Reproducible builds verification
- [ ] Hermetic build environment

### 16. Advanced Security
- [ ] Runtime security (Falco/Tetragon)
- [ ] Admission controller for image signatures (Kyverno verifyImages)
- [ ] Secret rotation automation (90-day max)

### 17. Performance Optimization
- [ ] Load test with k6 (target: 1000 RPS, p99 < 500ms)
- [ ] Optimize database indexes (pg_stat_statements)
- [ ] Enable query plan caching
- [ ] CDN for static assets (Cloudflare/CloudFront)

---

## Verification Checklist (Run Before Each Release)

```bash
# 1. Code Quality
make lint && make typecheck && make format:check

# 2. Tests
make test && make test-cov

# 3. Security Scans
cd apps/api && pip-audit --desc --format=json && bandit -r app/
cd apps/web && npm audit --audit-level=high

# 4. Container Scans
docker build -t astra-api:test -f apps/api/Dockerfile apps/api/
docker build -t astra-web:test -f apps/web/Dockerfile .
trivy image --severity CRITICAL,HIGH astra-api:test
trivy image --severity CRITICAL,HIGH astra-web:test

# 5. K8s Policy Check
kyverno apply k8s/ --dry-run

# 6. Build Verification
docker compose -f docker/prod/docker-compose.yml build
docker compose -f docker/prod/docker-compose.yml config

# 7. Dependency Review
pip list --outdated && npm outdated
```

---

## Files Created/Modified in This Session

| File | Status | Description |
|------|--------|-------------|
| `docker/prod/docker-compose.yml` | ✅ Modified | Updated to use production Dockerfiles |
| `apps/web/Dockerfile` | ✅ Created | Production multi-stage Dockerfile |
| `apps/web/next.config.ts` | ✅ Verified | Already has `output: 'standalone'` |
| `apps/web/src/app/api/health/route.ts` | ✅ Verified | Health endpoint exists |

---

## Next Steps (Immediate)

1. **Test production Docker build:**
   ```bash
   cd /Users/neominnthu/Desktop/Project/agency/astra-os
   docker compose -f docker/prod/docker-compose.yml build
   ```

2. **Create SSL certs for local prod testing:**
   ```bash
   mkdir -p docker/prod/ssl
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout docker/prod/ssl/key.pem \
     -out docker/prod/ssl/cert.pem \
     -subj "/CN=localhost"
   ```

3. **Create `.env.production` from template and test:**
   ```bash
   cp docker/prod/.env.example docker/prod/.env
   # Edit with real values
   docker compose -f docker/prod/docker-compose.yml --env-file docker/prod/.env up -d
   ```

4. **Run security scans locally** (see Critical Actions #5)

5. **Push to trigger CI/CD** and verify GitHub Actions pass

---

## Architecture Decisions Record (ADRs)

| ADR | Title | Status |
|-----|-------|--------|
| 001 | Use distroless base images for Python services | ✅ Accepted |
| 002 | Kustomize for K8s environment management | ✅ Accepted |
| 003 | Kyverno for Pod Security Standards enforcement | ✅ Accepted |
| 004 | GitHub Actions + Cosign for image signing | ✅ Accepted |
| 005 | External Secrets Operator for secret management | 🔄 Planned |
| 006 | OpenTelemetry for unified observability | ✅ Accepted |
| 007 | Temporal for workflow orchestration | ✅ Accepted |

---

*This document should be updated as hardening progresses. Review monthly.*