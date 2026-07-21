# Changelog - Astra OS

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive CI/CD pipeline with security scanning, testing, and deployment
- Automated version management with semantic versioning
- Release workflow with dry-run support and GitHub Release creation
- Development guide (DEVELOPMENT.md) with full contributing guidelines
- Version management script with dry-run support and prerelease handling

### Changed
- Improved CI/CD workflow organization with 10 distinct stages
- Enhanced security scanning (Bandit, TruffleHog, Semgrep, Trivy, pip-audit, npm audit)
- Updated Docker configuration for multi-arch builds (amd64/arm64)

### Security
- Added Cosign image signing in CI/CD
- Added Trivy container vulnerability scanning
- Added Hadolint Dockerfile linting
- Added scheduled weekly security scans

---

## [1.1.1] - 2026-07-21

### Fixed
- **Test Infrastructure**: Fixed 1,436/1,436 test suite — resolved SocialIntelligence nested enum (LINKEDIN), ShadowMode constructor signature mismatch, and 4 test expectation mismatches
- **Social Platform Enum**: Un-nested duplicate `SocialPlatform` class that hid LINKEDIN, TWITTER, TIKTOK, YOUTUBE, GOOGLE members
- **Shadow Mode Tests**: Fixed `decision_types` missing from test ShadowSession objects, corrected `end_session` status assertion (DISABLED→ARCHIVED), fixed `agreement_rate` calculation, consolidated fixture for LiftMeasurementService
- **Social Intelligence Tests**: Aligned `test_detect_spam`, `test_detect_lead_intent`, `test_spam_score_calculation`, and `test_language_detection` expectations with analyzer algorithm behavior
- **Docker**: Converted both API and Worker Dockerfiles to deterministic `uv sync --frozen` multi-stage builds with distroless-like runtime

### Changed
- **Version Alignment**: Web (0.0.1→1.1.0) and CLI (0.1.0→1.1.0) packages bumped to match API v1.1.0
- **Repo Hygiene**: Removed committed bandit scan reports (2.4MB), `.bak`/`.orig` backup files, and `.db-journal` artifacts
- **Web Dashboard**: Refactored dashboard page with React Query, anomaly detection, forecasting panel, and widget grid system
- **Gitignore**: Added patterns for security scan reports, backup files, and generated configs

### Maintenance
- Cleaned up 2.4MB of committed security scan artifacts
- Removed stale backup files (.bak, .orig) from agent orchestrator tests

---

## [1.0.0] - 2024-07-15

### Added
- **Core Architecture**: Clean Architecture with DDD, event-driven, multi-tenant
- **Agent Orchestration**: Hierarchical agents (CEO, Directors, Specialists) with ReAct loops
- **Governance System**: Autonomy levels (ADVISORY, SEMI_AUTO, FULL_AUTO) with spend limits
- **Resilience Patterns**: Circuit breakers, retry policies, bulkheads, dead letter queues
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging
- **API Layer**: FastAPI with async SQLAlchemy, Redis caching, Temporal workflows
- **Web Frontend**: Next.js 14 with React 18, TypeScript, Tailwind CSS
- **Authentication**: JWT with refresh tokens, RBAC, organization multi-tenancy
- **Content Generation**: AI-powered content templates, brand voices, SEO scoring
- **Campaign Management**: Full lifecycle (draft → active → paused → completed → archived)
- **Budget Pacing**: Multiple strategies (even, front-loaded, back-loaded, adaptive)
- **Agent Communication**: Event bus, handoff manager, audit trails
- **Memory System**: In-memory with consolidation, knowledge graph integration

### Infrastructure
- **Kubernetes**: Production-ready manifests with Kustomize overlays (dev/staging/prod)
- **Docker**: Multi-stage hardened images (distroless runtime, non-root)
- **CI/CD**: GitHub Actions with 10-stage pipeline (lint, security, test, build, deploy)
- **Security**: Bandit, TruffleHog, Semgrep, Trivy, pip-audit, npm-audit, Cosign signing
- **Monitoring**: OpenTelemetry, Prometheus, Grafana dashboards, SLOs with burn-rate alerting

### Developer Experience
- Pre-commit hooks (Ruff, MyPy, Bandit)
- Comprehensive test suite (unit, integration, E2E)
- Development guide with full contributing guidelines
- Automated version management and release workflows

### Security
- JWT authentication with refresh token rotation
- RBAC with organization-scoped permissions
- Rate limiting (API 30r/s, Auth 5r/m)
- CSP, HSTS, security headers via nginx
- Secrets scanning (TruffleHog) and dependency auditing (pip-audit, npm audit)

---

## [0.3.0] - 2024-06-01

### Added
- Content publishing scheduler with cron support
- Recurring content workflows
- Social media integration (Meta, LinkedIn, TikTok)
- Google Ads API integration
- LinkedIn Ads API integration

### Changed
- Improved agent hierarchy with better delegation rules
- Enhanced budget pacing algorithms

### Fixed
- Memory leak in event bus subscription cleanup
- Race condition in budget pacing concurrent updates

---

## [0.2.0] - 2024-04-15

### Added
- Multi-tenant organization support
- Team member management with roles
- Feature flags per organization
- Billing plans with usage tracking
- Audit logging for compliance

### Changed
- Refactored agent orchestration for better testability
- Migrated to async SQLAlchemy 2.0

### Security
- Added refresh token rotation
- Implemented RBAC with granular permissions

---

## [0.1.0] - 2024-02-01

### Added
- Initial project structure
- Basic agent framework
- FastAPI foundation
- PostgreSQL + Redis setup
- Basic authentication

---

## Version History Summary

| Version | Date | Type | Key Highlights |
|---------|------|------|----------------|
| 1.0.0 | 2024-07-15 | Major | Production-ready, full CI/CD, K8s, security hardening |
| 0.3.0 | 2024-06-01 | Minor | Content scheduling, ad platform integrations |
| 0.2.0 | 2024-04-15 | Minor | Multi-tenancy, RBAC, billing |
| 0.1.0 | 2024-02-01 | Initial | Project foundation |

---

## Upgrade Guides

### 0.x → 1.0.0
**Breaking Changes:**
- API response format standardized (envelope with `data`, `meta`, `errors`)
- Agent autonomy config moved to `AutonomyConfig` entity
- Budget pacing strategies renamed (see migration guide)
- Database schema changes require migration

**Migration Steps:**
```bash
# 1. Backup database
pg_dump $DATABASE_URL > backup.sql

# 2. Run migrations
alembic upgrade head

# 3. Verify
python -m pytest tests/integration/ -v
```

### 0.2.x → 0.3.0
- Content scheduling API changed (new cron format)
- Ad platform adapters require new credentials format

### 0.1.x → 0.2.0
- Multi-tenancy requires organization_id on all entities
- Auth middleware updated (new header format)

---

## Release Process

### Patch Release (Bug Fixes)
```bash
# 1. Create hotfix branch from main
git checkout -b hotfix/issue-123 main

# 2. Fix, test, commit
# ...

# 3. Release
python .github/scripts/version.py release patch

# 4. Push
git push origin main --tags
```

### Minor Release (Features)
```bash
# 1. Create release branch from develop
git checkout -b release/v1.2.0 develop

# 2. Version bump, final QA
python .github/scripts/version.py release minor

# 4. Merge to main, deploy staging
# 5. Create GitHub Release
gh release create v1.2.0 --generate-notes
```

### Major Release (Breaking Changes)
```bash
# 1. Create release branch from develop
git checkout -b release/v2.0.0 develop

# 2. Update docs, migration guides
# 3. Version bump
python .github/scripts/version.py release major

# 4. Extended testing period
# 5. Production deploy with monitoring
```

---

## Maintainers

- **Lead Architect**: [@webbixray](https://github.com/webbixray)
- **Core Team**: Astra OS Contributors

## Support

- **Issues**: [GitHub Issues](https://github.com/webbixray/astra-os/issues)
- **Discussions**: [GitHub Discussions](https://github.com/webbixray/astra-os/discussions)
- **Security**: [Security Policy](SECURITY.md)
