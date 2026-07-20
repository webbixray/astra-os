# Astra OS

![CI/CD](https://github.com/webbixray/astra-os/actions/workflows/ci-cd.yaml/badge.svg)
![Docker](https://github.com/webbixray/astra-os/actions/workflows/docker.yml/badge.svg)
![Tests](https://img.shields.io/badge/tests-1200%2B%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Node](https://img.shields.io/badge/node-20-brightgreen)
![Security](https://img.shields.io/badge/security-Bandit%2C%20Trivy%2C%20Semgrep-success)
![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue)

**AI-Native Marketing & Business Growth OS** — AI agents, workflow automation, multi-platform ad management, content generation, analytics.

## Quick Start
```bash
git clone https://github.com/webbixray/astra-os.git && cd astra-os
cp docker/dev/.env.example .env
make dev
```
After startup: **API** http://localhost:8000/docs | **Web** http://localhost:3000 | **Temporal** http://localhost:8233

## Docker Production
```bash
make docker-build-prod      # Build API + Web + Worker images
./deploy.sh up              # Deploy full production stack
./deploy.sh backup          # Database backup
```

**Production Stack:** Nginx → API (×2) + Web (×2) + Worker | Postgres 16 + Redis 7 + Temporal | Prometheus + Grafana + Loki + Tempo + Alertmanager + OTel Collector

## Architecture
```
Web (Next.js) → API (FastAPI) → Postgres + Redis + Temporal
  └─ Middleware: Auth · CSRF · RateLimit · Audit · OTel · Security Headers
  └─ Clean Architecture: domain → application → infrastructure → presentation
  └─ Agents: Hierarchical (CEO → Directors → Specialists), autonomy levels
```

## Testing
```bash
make test       # All tests
make test-api   # Python API tests (1200+)
make test-web   # Vitest frontend
make test-e2e   # Playwright E2E
make test-load  # k6 load tests
```

## Security
```bash
make security-scan  # Bandit SAST
```
15-layer security: JWT auth, RBAC, CSRF HMAC, rate limiting, CSP/HSTS headers, AES-256-GCM encryption, distroless containers, Cosign signatures, SBOM.

## CI/CD (11 Stages)
Lint → Security (Bandit, Semgrep, TruffleHog) → Container Scan (Trivy, Hadolint) → Tests → Build + Push (GHCR, multi-arch) → Cosign Sign → SBOM → Deploy Staging → Deploy Production (canary) → Post-Deploy Validation → Weekly Scheduled Scan

## Project Structure
```
apps/api/         FastAPI backend (Clean Architecture, 30+ route modules)
apps/web/         Next.js 15 frontend (React 19, Turbopack)
services/         Agent orchestrator (hierarchical AI agents)
packages/ui/      Shared React components
docker/           Dev + Prod + Monitoring compose stacks
k8s/              Kubernetes manifests (Kustomize, ArgoCD, Kyverno)
docs/             Architecture, ADRs, API reference, deployment guides
.github/          CI/CD workflows, Dependabot, issue templates
```

## Docs
[Architecture](docs/ARCHITECTURE.md) | [API Reference](docs/API_REFERENCE.md) | [Deployment](docs/DEPLOYMENT.md) | [Roadmap](docs/ROADMAP.md) | [Production Checklist](PRODUCTION_READINESS_CHECKLIST.md) | [ADR Index](docs/phase-1/adr/ADR-INDEX.md) | [Security](SECURITY.md)

Built by **Hermes Dev Studio**.
