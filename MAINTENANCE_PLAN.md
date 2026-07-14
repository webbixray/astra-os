# ASTRA OS — Long-Term Maintenance & Evolution Plan

> **Scope:** 5-year roadmap (2025–2030) for continuous delivery, reliability, and feature evolution.
> **Role:** Senior Platform Engineering Agency — we own the full lifecycle: architecture, implementation, testing, deployment, observability, and on-call.

---

## 🎯 Guiding Principles

| Principle | How We Enforce It |
|-----------|-------------------|
| **Zero-downtime releases** | Blue/green deployments, backwards-compatible DB migrations, feature flags |
| **Test-first (TDD)** | Every change starts with a failing test; CI blocks merge on red |
| **Observability by default** | Structured logs (JSON), OpenTelemetry traces, Prometheus metrics, SLO dashboards |
| **Security as code** | Dependabot + pip-audit + bandit + trivy in CI; secrets only in Vault/1Password |
| **Documentation lives with code** | ADRs in `docs/adr/`, API specs in OpenAPI, runbooks in `docs/runbooks/` |
| **Automate everything** | `make check` = lint + typecheck + test; `make release` = version bump + changelog + tag + deploy |

---

## 📦 Versioning Strategy

### Semantic Versioning (SemVer) — `MAJOR.MINOR.PATCH`

| Segment | When to Bump | Example |
|---------|--------------|---------|
| **MAJOR** | Breaking API changes, DB schema removals, removed config keys | `1.0.0 → 2.0.0` |
| **MINOR** | New features, new endpoints, new config (opt-in), deprecated but supported | `1.0.0 → 1.1.0` |
| **PATCH** | Bug fixes, security patches, internal refactors, doc updates | `1.0.0 → 1.0.1` |

### Release Cadence

| Channel | Frequency | Branch | Audience |
|---------|-----------|--------|----------|
| **Canary** | Every merge to `main` | `main` | Internal staging |
| **Release Candidate** | Weekly (Mondays) | `release/vX.Y` | Design partners |
| **Stable** | Monthly (1st Tuesday) | `vX.Y.Z` tags | All customers |
| **LTS** | Every 6 months | `lts/vX.Y` | Enterprise (24-mo support) |

### Version File

```toml
# pyproject.toml (single source of truth)
[project]
version = "0.1.0"
```

Bumped via: `make bump-{major,minor,patch}` → updates `pyproject.toml`, `CHANGELOG.md`, creates git tag.

---

## 📋 Changelog Format (Keep a Changelog + Conventional Commits)

### File: `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New AI content generation templates for LinkedIn carousel posts (#142)
- Webhook retry with exponential backoff for publishing adapters (#138)

### Changed
- Increased default publishing poll interval from 30s → 60s (configurable) (#135)

### Deprecated
- `POST /content/{id}/publish` without `platform` field (use multi-platform endpoint) (#140)

### Removed
- Legacy `campaign_templates` table (migrated to `content_templates`) (#130)

### Fixed
- Race condition in `ContentPublishingScheduler` when multiple workers process same batch (#145)
- Memory leak in Temporal workflow replay for long-running campaigns (#132)

### Security
- Updated `pydantic` to 2.9.2 (CVE-2024-XXXXX) (#139)
```

### Commit Message Convention (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | Changelog Section |
|------|-------------------|
| `feat` | Added |
| `fix` | Fixed |
| `refactor` | Changed (if user-visible) |
| `perf` | Changed |
| `deprecate` | Deprecated |
| `remove` | Removed |
| `security` | Security |
| `docs` | (not in changelog) |
| `test` | (not in changelog) |
| `chore` | (not in changelog) |
| `ci` | (not in changelog) |

**Scopes:** `api`, `publishing`, `scheduler`, `ai`, `workflows`, `auth`, `db`, `infra`, `ui`, `docs`

**Examples:**
```
feat(publishing): add multi-platform publish endpoint
fix(scheduler): prevent duplicate processing of scheduled content
security(deps): update pydantic to 2.9.2 (CVE-2024-XXXXX)
deprecate(api): remove legacy single-platform publish endpoint
```

---

## 🔧 CI/CD Pipeline (`.github/workflows/`)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, release/**]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v2
      - uses: astral-sh/uv-action@v1
      - run: uv run ruff check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/uv-action@v1
      - run: uv run mypy app/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_PASSWORD: test }
        ports: [5432:5432]
      redis:
        image: redis:7-alpine
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/uv-action@v1
      - run: uv run pytest -n auto --cov=app --cov-report=xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pypa/gh-action-pip-audit@v1
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
      - uses: github/codeql-action/upload-sarif@v3

  build:
    needs: [lint, typecheck, test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          push: false
          tags: astra-api:${{ github.sha }}
```

### Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      version:
        type: choice
        options: [patch, minor, major]
        required: true

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: astral-sh/uv-action@v1
      - run: |
          uv run python scripts/bump_version.py ${{ github.event.inputs.version }}
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git commit -am "chore: release v$(cat pyproject.toml | grep version | cut -d'\"' -f2)"
          git tag v$(cat pyproject.toml | grep version | cut -d'\"' -f2)
          git push origin main --tags
      - uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

---

## 🗓️ 5-Year Roadmap

### Phase 1: Foundation (Months 1–6) — **v0.x → v1.0**
| Epic | Stories | Target |
|------|---------|--------|
| **Core Stability** | Fix all P0 bugs, harden scheduler, add DLQ for failed publishes | v0.5 |
| **Observability** | OpenTelemetry tracing, SLO dashboards (latency, error rate, publish success), alerting rules | v0.6 |
| **Security Hardening** | Penetration test, secret scanning, RBAC audit, API rate limiting | v0.7 |
| **Developer Experience** | `make dev` spins up full stack, API docs (OpenAPI), local Temporal UI | v0.8 |
| **GA Release** | Migration guide, runbooks, on-call rotation, customer onboarding docs | **v1.0** |

### Phase 2: Platform Maturity (Months 7–18) — **v1.x → v2.0**
| Epic | Stories |
|------|---------|
| **Multi-region** | Active-active deployment (AWS + GCP), read replicas, CDN for media |
| **Advanced AI** | Fine-tuned brand voice models, A/B testing for content, predictive best-time-to-post |
| **Workflow Engine v2** | Visual builder, conditional branches, human-in-the-loop approvals, replay |
| **Analytics Platform** | Unified dashboard (campaigns + content + ads), custom reports, data export |
| **Enterprise SSO** | SAML/OIDC, SCIM provisioning, audit logs, compliance reports (SOC2) |

### Phase 3: Ecosystem & Scale (Months 19–36) — **v2.x → v3.0**
| Epic | Stories |
|------|---------|
| **Plugin Marketplace** | 3rd-party adapters (TikTok, Pinterest, WhatsApp), webhook registry, revenue share |
| **AI Agents** | Autonomous campaign optimization, budget pacing, creative fatigue detection |
| **Data Lake** | Snowflake/BigQuery sync, ML feature store, customer 360° view |
| **White-label** | Custom domains, theming, API-only mode, reseller portal |
| **Global Compliance** | GDPR/CCPA tooling, data residency, encryption key management |

### Phase 4: Intelligence & Autonomy (Months 37–60) — **v3.x → v4.0**
| Epic | Stories |
|------|---------|
| **Generative Campaigns** | Prompt → full campaign (content + ads + calendar + budget) |
| **Predictive Growth** | LTV modeling, churn prediction, channel mix optimization |
| **Self-healing Infra** | Auto-scaling, chaos engineering, automated failover drills |
| **Federated Learning** | Cross-customer model improvements without data sharing |

---

## 🏗️ Technical Debt & Refactoring Budget

| Quarter | Budget | Focus |
|---------|--------|-------|
| Q1 | 15% | Scheduler reliability, test coverage >90% |
| Q2 | 20% | Temporal migration, workflow v2 foundation |
| Q3 | 15% | API versioning, deprecation pipeline |
| Q4 | 20% | Multi-region prep, data lake schema |

**Rule:** Any refactor >2 days requires an ADR and tech-lead approval.

---

## 📐 Architecture Decision Records (ADRs)

Location: `docs/adr/`

### Template
```markdown
# ADR-<NNN>: <Title>

**Status:** Proposed | Accepted | Superseded
**Date:** YYYY-MM-DD
**Deciders:** @lead1, @lead2
**Technical Lead:** @author

## Context
What problem are we solving? What constraints exist?

## Decision
What are we doing? Include diagrams if helpful.

## Consequences
### Positive
- ...
### Negative
- ...
### Risks
- ...

## Alternatives Considered
1. ...
2. ...

## Implementation Plan
- [ ] Task 1
- [ ] Task 2

## Rollback Plan
How to revert if wrong.
```

### Existing ADRs (to create)
| ID | Title | Status |
|----|-------|--------|
| 001 | Use Temporal for Workflow Orchestration | Accepted |
| 002 | PostgreSQL + JSONB for Content Storage | Accepted |
| 003 | In-process Scheduler vs External (APScheduler/Celery) | Accepted |
| 004 | OpenTelemetry for Observability | Accepted |
| 005 | Feature Flags via Config + DB | Proposed |

---

## 🧪 Testing Strategy

### Test Pyramid
```
           E2E (10%)     ← Playwright, real browser, staging
          /       \
   Integration (30%)  ← API + DB, Temporal, Redis
  /           \
Unit (60%)    ← Pure functions, domain logic, mocks
```

### Coverage Targets
| Layer | Target | Tool |
|-------|--------|------|
| Unit | 95% | pytest + coverage |
| Integration | 80% | pytest + testcontainers |
| E2E | Critical paths only | Playwright |
| Contract | 100% (public API) | Schemathesis |

### Mutation Testing
```bash
uv run mutmut run --paths-to-mutate=app/domain/
# Target: >80% mutation score
```

### Property-Based Testing
```python
# tests/contract/test_publishing_scheduler.py
from hypothesis import given, strategies as st
from app.domain.entities.content.content_publish import ContentPublish

@given(st.uuids(), st.text(min_size=1, max_size=50))
def test_publish_idempotency(publish_id, platform):
    # Publishing same content twice with same ID is idempotent
    ...
```

---

## 📊 Observability & SLOs

### Service Level Objectives
| Service | SLO | Measurement | Alert |
|---------|-----|-------------|-------|
| API (p99 latency) | < 500ms | HTTP latency histogram | Page if >5% breach |
| Publish Success Rate | > 99.5% | `published_total / scheduled_total` | Page if <99% |
| Scheduler Lag | < 60s | `now() - scheduled_at` for due items | Warn if >2min |
| AI Generation Latency | < 10s | LLM request duration | Warn if p95 > 15s |
| Availability | 99.9% | Uptime checks | Page on downtime |

### Dashboards (Grafana)
- **API Health** — latency, error rate, throughput, saturation (RED)
- **Publishing Pipeline** — queue depth, success/failure, adapter latency
- **Scheduler** — due items, processing time, batch sizes
- **AI Usage** — tokens, cost, latency by model/provider
- **Business** — active orgs, content created, campaigns launched

### Alerting (PrometheusRule)
```yaml
groups:
- name: astra-api
  rules:
  - alert: HighPublishFailureRate
    expr: |
      rate(publish_failed_total[5m]) / rate(publish_attempted_total[5m]) > 0.01
    for: 2m
    labels: {severity: critical}
    annotations:
      summary: "Publish failure rate > 1%"
```

---

## 🔐 Security Practices

### Dependency Management
```bash
# Weekly automated PR via Dependabot
# Blocking: pip-audit in CI
# Allowlist: only approved licenses (MIT, Apache-2.0, BSD-3)
```

### Secrets
| Secret | Storage | Rotation |
|--------|---------|----------|
| DB passwords | 1Password / Vault | 90 days |
| API keys (OpenAI, Meta, etc.) | 1Password | 90 days |
| JWT signing keys | KMS (AWS/GCP) | 365 days |
| Webhook secrets | Vault + env injection | Per-deployment |

### Compliance
- **SOC2 Type II** — Target Q4 2025
- **GDPR** — Data export/delete endpoints, DPA template
- **Pen Test** — Annual (external) + quarterly (internal)

---

## 🚀 Deployment Architecture

### Environments
| Env | Purpose | URL | Data |
|-----|---------|-----|------|
| `local` | Developer laptop | `http://localhost:8000` | SQLite / pg in container |
| `staging` | Integration + E2E | `https://staging.astra.internal` | Scrubbed prod subset |
| `canary` | 5% traffic | `https://canary.astra.io` | Prod (read-only) |
| `prod` | 100% traffic | `https://api.astra.io` | Prod |

### Infrastructure (Terraform)
```
infra/
├── modules/
│   ├── vpc/
│   ├── rds-postgres/
│   ├── elasticache-redis/
│   ├── ecs-fargate/
│   ├── alb/
│   ├── temporal/
│   └── monitoring/
├── envs/
│   ├── staging/
│   ├── canary/
│   └── prod/
└── root.tf
```

### Deployment Strategy
```bash
# Canary (auto on RC tag)
make deploy ENV=canary VERSION=v1.2.0-rc.1

# Blue/Green (prod)
make deploy ENV=prod VERSION=v1.2.0 STRATEGY=bluegreen

# Rollback (instant)
make rollback ENV=prod PREVIOUS=v1.1.5
```

---

## 🛠️ Developer Experience (DX)

### One-Command Setup
```bash
git clone git@github.com:org/astra-os.git
cd astra-os
make bootstrap  # installs uv, deps, starts docker infra, runs migrations, seeds DB
make dev        # starts API (uvicorn --reload) + Web (next dev) + Temporal UI
```

### Useful Make Targets
```makefile
check: lint typecheck test           # Runs in CI
lint: ruff check . && ruff format --check .
typecheck: mypy app/
test: pytest -n auto --cov=app
test-watch: ptw --runner "pytest -x"
db-migrate: alembic upgrade head
db-seed: python scripts/seed_db.py
release-patch: uv run python scripts/bump_version.py patch
release-minor: uv run python scripts/bump_version.py minor
release-major: uv run python scripts/bump_version.py major
```

### Pre-commit Hooks (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        args: [--strict]
  - repo: local
    hooks:
      - id: pytest-changed
        name: pytest on changed files
        entry: bash -c 'pytest $(git diff --name-only HEAD | grep "tests/" | head -20)'
        language: system
```

---

## 📁 Repository Structure (Canonical)

```
astra-os/
├── .github/
│   ├── workflows/          # CI, Release, Security
│   └── dependabot.yml
├── apps/
│   ├── api/                # FastAPI backend (this plan)
│   │   ├── app/
│   │   │   ├── domain/         # Pure Python, no deps
│   │   │   │   ├── entities/
│   │   │   │   ├── services/
│   │   │   │   ├── events/
│   │   │   │   └── exceptions/
│   │   │   ├── application/    # Use cases, ports
│   │   │   │   └── use_cases/
│   │   │   ├── infrastructure/ # Adapters, DB, External APIs
│   │   │   │   ├── db/
│   │   │   │   ├── temporal/
│   │   │   │   ├── publishing/
│   │   │   │   └── ai/
│   │   │   ├── presentation/   # API layer
│   │   │   │   ├── routes/
│   │   │   │   ├── middleware/
│   │   │   │   └── schemas/
│   │   │   ├── config.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── contract/
│   │   ├── scripts/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── web/                # Next.js frontend
├── infra/                  # Terraform
├── docs/
│   ├── adr/
│   ├── runbooks/
│   └── api/
├── scripts/                # Shared utilities
├── CHANGELOG.md
├── MAINTENANCE_PLAN.md     # This file
├── Makefile
├── docker-compose.yml
└── pyproject.toml          # Root (optional, for workspace)
```

---

## 📋 Current Sprint Backlog (v0.2 → v0.5)

| ID | Title | Type | Est. | Owner | Status |
|----|-------|------|------|-------|--------|
| ENG-145 | Fix scheduler duplicate processing race | Bug | 2d | @backend-lead | 🔄 In PR |
| ENG-138 | Add exponential backoff to publishing webhooks | Feat | 3d | @backend-2 | 📋 Ready |
| ENG-142 | LinkedIn carousel content template | Feat | 1d | @ai-eng | ✅ Done |
| ENG-135 | Make scheduler poll interval configurable | Chore | 1d | @backend-lead | ✅ Done |
| ENG-140 | Deprecate single-platform publish endpoint | Deprecate | 2d | @backend-1 | 📋 Ready |
| ENG-139 | Security: Update pydantic (CVE) | Security | 1d | @sec | ✅ Done |
| ENG-132 | Fix Temporal workflow memory leak | Bug | 5d | @infra | 🔄 In Progress |
| ENG-130 | Migrate campaign_templates → content_templates | Refactor | 3d | @backend-2 | ✅ Done |

---

## 📞 On-Call & Incident Response

### Rotation
- **Primary:** Week-long, follows sun (US/EU/APAC)
- **Secondary:** Backup, same week
- **Escalation:** Tech Lead → Engineering Manager → VP Eng

### Runbooks (`docs/runbooks/`)
| Runbook | Trigger | Owner |
|---------|---------|-------|
| `scheduler-stuck.md` | No publishes for >5min | Primary |
| `publish-failures-spike.md` | Failure rate >1% | Primary |
| `temporal-outage.md` | Temporal cluster down | Infra |
| `db-connection-exhaustion.md` | Pool >90% | Primary |
| `ai-cost-spike.md` | Daily tokens > budget | AI Eng |

### Postmortem Template
```markdown
# Incident YYYY-MM-DD-<slug>

**Severity:** SEV-1/2/3
**Duration:** Xh Ym
**Impact:** <user-facing description>

## Timeline
- HH:MM — Detected via <alert>
- HH:MM — <action taken>
- HH:MM — Resolved

## Root Cause
<5 Whys analysis>

## Action Items
- [ ] <fix> — Owner — Due date
- [ ] <prevention> — Owner — Due date

## Lessons Learned
...
```

---

## 🤝 Agency Engagement Model

| Activity | Cadence | Deliverable |
|----------|---------|-------------|
| **Sprint Planning** | Bi-weekly (Mon) | Sprint goal, committed stories |
| **Standup** | Daily (async) | Blocker escalation |
| **Demo** | Bi-weekly (Fri) | Working software, stakeholder feedback |
| **Retro** | Bi-weekly (Fri) | 3 improvements → action items |
| **Architecture Review** | Monthly | ADRs, tech debt decisions |
| **Security Review** | Quarterly | Threat model, pen test scope |
| **Capacity Planning** | Quarterly | Infra scaling, hiring plan |
| **Roadmap Review** | Quarterly | Next quarter OKRs, epic prioritization |

### Communication Channels
| Channel | Purpose |
|---------|---------|
| `#astra-eng` | Daily coordination, alerts |
| `#astra-incidents` | SEV-1/2 only, war room |
| `#astra-releases` | Deploy notifications, changelog |
| `#astra-ai` | Model experiments, prompt engineering |
| `Notion` | Sprint board, docs, decisions |

---

## ✅ Definition of Done (per Story)

- [ ] Code compiles, `make check` passes
- [ ] Unit tests added/updated (≥90% coverage on new code)
- [ ] Integration test for API changes
- [ ] OpenAPI spec updated
- [ ] CHANGELOG entry added (conventional commit)
- [ ] Docs updated (ADR if architectural, runbook if operational)
- [ ] Feature flag added (if user-facing)
- [ ] Deployed to staging, smoke tested
- [ ] Code reviewed by 1+ engineer
- [ ] Merged to `main` (triggers canary)

---

## 📈 Success Metrics (Agency KPIs)

| Metric | Target | Review |
|--------|--------|--------|
| **Deploy Frequency** | ≥ 10/day (canary) | Weekly |
| **Lead Time (commit→prod)** | < 2 hours | Weekly |
| **Change Failure Rate** | < 1% | Monthly |
| **MTTR** | < 30 min (SEV-1) | Monthly |
| **Test Coverage** | > 90% (unit), > 80% (integration) | Per PR |
| **Security Vulnerabilities** | 0 critical, < 5 high | Continuous |
| **Technical Debt Ratio** | < 5% (SonarQube) | Quarterly |
| **Customer-reported Bugs** | < 2/month | Monthly |

---

## 📝 Appendices

### A. Version Bump Script (`scripts/bump_version.py`)
```python
#!/usr/bin/env python3
"""Bump version in pyproject.toml and update CHANGELOG.md"""
import re
import sys
import subprocess
from pathlib import Path
from datetime import date

TOML = Path("pyproject.toml")
CHANGELOG = Path("CHANGELOG.md")

def current_version() -> str:
    text = TOML.read_text()
    m = re.search(r'version\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else "0.0.0"

def bump(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major": major, minor, patch = major + 1, 0, 0
    elif part == "minor": minor, patch = minor + 1, 0
    elif part == "patch": patch += 1
    return f"{major}.{minor}.{patch}"

def update_toml(new_version: str):
    text = TOML.read_text()
    text = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', text)
    TOML.write_text(text)

def update_changelog(new_version: str):
    today = date.today().isoformat()
    header = f"## [{new_version}] - {today}\n\n"
    # Insert after "# Changelog\n\n## [Unreleased]"
    text = CHANGELOG.read_text()
    text = text.replace("## [Unreleased]\n\n", f"## [Unreleased]\n\n{header}")
    CHANGELOG.write_text(text)

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"major", "minor", "patch"}:
        print("Usage: bump_version.py <major|minor|patch>")
        sys.exit(1)

    part = sys.argv[1]
    old = current_version()
    new = bump(old, part)
    print(f"Bumping {old} → {new} ({part})")
    update_toml(new)
    update_changelog(new)
    subprocess.run(["git", "add", "pyproject.toml", "CHANGELOG.md"], check=True)
```

### B. Release Checklist (`scripts/release_checklist.md`)
```
## Pre-Release
- [ ] All CI checks green on `release/vX.Y` branch
- [ ] CHANGELOG.md reviewed and approved
- [ ] Version bumped (`make release-patch|minor|major`)
- [ ] Git tag created: `git tag vX.Y.Z && git push origin vX.Y.Z`
- [ ] GitHub Release drafted with auto-generated notes
- [ ] Staging deployed and smoke-tested

## Release
- [ ] Canary deployed (5% traffic), monitored 30min
- [ ] Gradual rollout: 25% → 50% → 100% (10min each)
- [ ] SLO dashboards green
- [ ] Error budgets not burning

## Post-Release
- [ ] Close milestone in GitHub
- [ ] Update `#astra-releases` with summary
- [ ] Schedule postmortem if any incidents
- [ ] Begin next sprint planning
```

---

*This plan is a living document. Update it every sprint retrospective and quarterly roadmap review.*
*Last updated: 2025-07-14 | Version: 1.0 | Owner: Platform Engineering Agency*