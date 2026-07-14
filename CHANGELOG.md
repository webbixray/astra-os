# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Astra CLI with comprehensive command coverage (agents, workflows, monitoring, costs, schemas, auth, config)
- Process supervisor for agent orchestrator with bounded restarts and crash-loop guard
- OpenTelemetry tracing with semantic conventions for agent spans
- Prometheus metrics with multi-window burn-rate alerting
- Circuit breaker pattern on Model Router fallback chain
- Redis Streams Dead Letter Queue with replay capability
- Grafana dashboards for agent performance, circuit breakers, DLQ, cost tracking
- SLO/SLI definitions with burn-rate alerts (fast/medium/slow)
- Backstage plugin architecture for developer portal
- Security policy (SECURITY.md) with responsible disclosure
- Contributing guide (CONTRIBUTING.md)
- CODEOWNERS for review routing
- Dependabot configuration for automated dependency updates
- Pre-commit hooks (ruff, mypy, bandit, trufflehog, hadolint, etc.)

### Changed
- Fixed Click duplicate option warnings in CLI commands
- Updated Python requirement to >=3.11 for CLI
- Improved CLI authentication flow with token refresh

### Security
- Added bandit SAST scanning
- Added trufflehog secrets detection
- Added pip-audit dependency vulnerability scanning
- Added hadolint Dockerfile linting

## [0.1.0] - 2025-07-14

### Added
- Initial project structure with Clean Architecture + DDD
- Agent Orchestrator service (FastAPI + Redis Pub/Sub)
- API Layer with CQRS/Event Sourcing
- Web Dashboard (React + TypeScript + Vite)
- Kubernetes manifests with Kustomize
- Monitoring stack (Prometheus, Grafana, Loki, Tempo)
- CI/CD pipelines (GitHub Actions)

---

## Release Notes Format

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes