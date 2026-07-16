# Astra OS - Production Hardening Action Plan

## Executive Summary

This project has excellent infrastructure foundations (K8s, CI/CD, monitoring, security policies) but several critical gaps remain for production readiness. This plan addresses them systematically.

---

## Critical Gaps Identified

| Area | Gap | Severity | Status |
|------|-----|----------|--------|
| **Docker Prod** | `docker/prod/docker-compose.yml` uses `Dockerfile.dev` instead of hardened `Dockerfile` | 🔴 Critical | ❌ Not Fixed |
| **Web Dockerfile** | No production Dockerfile for Next.js app | 🔴 Critical | ❌ Not Fixed |
| **Dependencies** | `pnpm install` not run, `node_modules` missing | 🔴 Critical | ❌ Not Fixed |
| **API Dependencies** | Python deps not installed in API | 🔴 Critical | ❌ Not Fixed |
| **Tests** | Not executed, coverage unknown | 🟡 High | ❌ Not Run |
| **Secrets** | `.env.example` used but no secrets management verified | 🟡 High | ⚠️ Partial |
| **K8s Base** | Base K8s resources may be missing | 🟡 High | ⚠️ Partial |

---

## Phase 1: Foundation Fixes (Do First)

### 1.1 Fix Docker Production Configuration
**File:** `docker/prod/docker-compose.yml`
**Issue:** Line 38-40 uses `Dockerfile.dev` instead of `Dockerfile`
**Fix:** Change to use the hardened distroless Dockerfile

### 1.2 Create Production Web Dockerfile
**File:** `apps/web/Dockerfile` (new)
**Requirements:**
- Multi-stage build (builder → runner)
- Non-root user
- Standalone output for Next.js
- Health checks
- Minimal attack surface

### 1.3 Install Dependencies
```bash
pnpm install --frozen-lockfile
cd apps/api && pip install -e ".[dev]"
```

### 1.4 Run Test Suite
```bash
pnpm test
cd apps/api && python -m pytest -v --cov=app
```

---

## Phase 2: Security Hardening

### 2.1 Container Security
- [ ] Verify distroless base images
- [ ] Non-root user (UID 65532)
- [ ] Read-only root filesystem
- [ ] Drop all capabilities
- [ ] SecurityContext in all K8s deployments

### 2.2 Supply Chain Security
- [ ] SBOM generation (Syft) - ✅ In CI
- [ ] Image signing (Cosign) - ✅ In CI
- [ ] Trivy scanning - ✅ In CI
- [ ] Hadolint Dockerfile linting - ✅ In CI
- [ ] Dependency scanning (pip-audit, npm audit) - ✅ In CI

### 2.3 Runtime Security
- [ ] Kyverno policies - ✅ Defined
- [ ] Network policies - ✅ Defined
- [ ] PodSecurity Standards - ✅ Restricted via Kyverno
- [ ] mTLS - ⚠️ Documented but not implemented

### 2.4 Secrets Management
- [ ] External Secrets Operator - ✅ K8s config exists
- [ ] Sealed Secrets - ❌ Not configured
- [ ] Vault integration - ❌ Not configured
- [ ] No secrets in Git - ✅ .gitignore + TruffleHog

---

## Phase 3: Reliability & Observability

### 3.1 Health Checks
- [ ] Liveness probe - ✅ Implemented
- [ ] Readiness probe - ✅ Implemented
- [ ] Startup probe - ✅ Implemented
- [ ] Database/Redis/Temporal connectivity checks - ✅ In health endpoint

### 3.2 Observability
- [ ] OpenTelemetry tracing - ✅ In main.py
- [ ] Prometheus metrics - ✅ In main.py
- [ ] Structured JSON logging - ✅ In main.py
- [ ] Sentry integration - ✅ In main.py
- [ ] Grafana dashboards - ⚠️ Referenced but not in repo

### 3.3 Resilience Patterns
- [ ] Circuit breakers - ✅ In services/resilience.py
- [ ] Rate limiting - ✅ In middleware
- [ ] Dead letter queues - ✅ Referenced in HARDENING_COMPLETE.md
- [ ] Retry with exponential backoff - ✅ tenacity in deps
- [ ] Bulkheads - ⚠️ Referenced but not verified

### 3.4 Chaos Engineering
- [ ] 10 experiments defined - ✅ k8s/chaos-experiments.yaml
- [ ] LitmusChaos integration - ⚠️ Referenced

---

## Phase 4: K8s Production Readiness

### 4.1 Base Resources (Verify Existence)
- [ ] namespace.yaml
- [ ] postgres-statefulset.yaml
- [ ] redis-deployment.yaml
- [ ] temporal-deployment.yaml
- [ ] api-deployment.yaml
- [ ] web-deployment.yaml
- [ ] worker-deployment.yaml
- [ ] ingress.yaml
- [ ] hpa.yaml
- [ ] network-policies.yaml
- [ ] kyverno-policies.yaml
- [ ] external-secrets.yaml

### 4.2 Overlays
- [ ] Local (dev) - ✅ Exists
- [ ] Preview - ✅ Exists
- [ ] Staging - ✅ Exists
- [ ] Production - ✅ Exists

### 4.3 Production-Specific
- [ ] Resource limits/requests tuned
- [ ] Replica counts appropriate
- [ ] PodDisruptionBudgets - ✅ In api-deployment.yaml
- [ ] TopologySpreadConstraints - ❌ Missing
- [ ] PriorityClasses - ❌ Missing

---

## Phase 5: CI/CD Pipeline Hardening

### 5.1 Pipeline Stages (✅ All Defined in .github/workflows/ci.yml)
1. Lint & Format
2. Security Scanning (Bandit, Semgrep, TruffleHog, pip-audit)
3. Container Security (Trivy, Hadolint)
4. SBOM Generation
5. Image Signing (Cosign)
6. Tests (Unit + Integration)
7. K8s Policy Check (Kyverno)
8. Deploy Staging (on develop branch)
9. Deploy Production (on main, with approval)

### 5.2 Missing/To Verify
- [ ] ArgoCD setup for GitOps
- [ ] Automated rollback on SLO breach
- [ ] Canary deployment strategy
- [ ] Database migration strategy in CI

---

## Phase 6: Implementation Tasks

### Immediate (This Session)
1. Fix `docker/prod/docker-compose.yml` to use hardened Dockerfile
2. Create `apps/web/Dockerfile` for production
3. Install dependencies (pnpm, pip)
4. Run test suite
5. Verify Docker builds work

### Short-term (Next Session)
1. Add TopologySpreadConstraints to K8s deployments
2. Add PriorityClasses
3. Verify all K8s base resources exist
4. Set up External Secrets Operator manifests
5. Add Sealed Secrets controller

### Medium-term
1. Implement mTLS (Linkerd/Istio)
2. Set up Grafana dashboards
3. Create runbooks for all alerts
4. Implement disaster recovery testing
5. SOC2 evidence automation

---

## Verification Commands

```bash
# Test Docker builds
docker build -f apps/api/Dockerfile apps/api
docker build -f apps/web/Dockerfile apps/web

# Run tests
cd apps/api && python -m pytest -v --cov=app --cov-report=term-missing
cd apps/web && npm run test

# Security scans
bandit -r apps/api/app
trivy fs .
trufflehog git file://. --only-verified
pip-audit

# K8s validation
kubectl apply -k k8s/overlays/production --dry-run=client
kyverno apply k8s/ --dry-run

# Docker Compose production
cd docker/prod && docker compose config
```

---

## Success Criteria

- [ ] All tests pass (>80% coverage)
- [ ] Docker images build and run locally
- [ ] Trivy: 0 CRITICAL, 0 HIGH vulnerabilities
- [ ] Bandit: 0 HIGH severity issues
- [ ] TruffleHog: 0 verified secrets
- [ ] K8s manifests validate with Kyverno
- [ ] Production docker-compose starts all services healthy
- [ ] Health endpoints return 200 for all services