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

## [0.2.0] - 2025-07-14

### Added
- Content Publishing Scheduler: Background worker that automatically publishes scheduled content to platforms (Website, Twitter, LinkedIn, Facebook, Instagram, Email)
- Configuration options: `content_publishing_poll_interval` (default 60s) and `content_publishing_batch_size` (default 10)
- Manual trigger endpoint: `POST /api/v1/content/publishing/scheduler/trigger`
- Scheduler status endpoint: `GET /api/v1/content/publishing/scheduler/status`
- Idempotent processing with "publishing" status guard to prevent duplicate publishes
- Batch commit with error isolation - failed items marked individually, batch commits per batch
- Comprehensive unit tests (12 test cases covering start/stop, due processing, adapter errors, batch processing, manual trigger)
- Clean FastAPI lifespan integration with graceful shutdown

### Changed
- Fixed `datetime.UTC` compatibility for Python 3.9+ (uses `timezone.utc` with noqa)
- Linting fixes: import sorting, unused imports removed, contextlib.suppress for CancelledError

### Fixed
- Scheduled content now actually publishes at the scheduled time (previously `find_scheduled_due()` existed but was never called)

## [0.3.0] - 2025-07-14

### Added
- Content Recurring Schedules: Full CRUD for recurring content publishing schedules with cron expressions
- ContentSchedule entity with cron validation, status management (active/paused/completed/error), run tracking
- REST API endpoints: create, list, get, update, pause, resume, delete, preview next runs, manual trigger
- Background ContentScheduleWorker that automatically processes due schedules and publishes content
- Integration with existing publishing adapters (Website, Twitter, LinkedIn, Facebook, Instagram, Email)
- Schedule state persistence with next_run_at, run_count, max_runs limits
- Configuration: `content_schedule_poll_interval` (default 60s), `content_schedule_batch_size` (default 10)
- Preview next run times for any schedule via API
- Manual trigger endpoint for processing due schedules on-demand

### Changed
- Enhanced ContentPublishingScheduler to use configurable poll interval and batch size
- ContentScheduleService now uses publishing repositories for actual content publishing
- Reused WorkflowScheduler's CronExpression for consistent cron parsing/evaluation

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