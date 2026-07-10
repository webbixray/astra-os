# ASTRA OS - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Field-level encryption (HMAC-SHA256 + XOR CTR stream cipher) for sensitive database fields
- EncryptedString, EncryptedText, EncryptedJSON SQLAlchemy TypeDecorator types
- X-RateLimit-* response headers for client-side throttling
- Audit logging infrastructure with structured logging
- 27 loading skeleton components for all dashboard sub-pages
- Loading.tsx for improved user experience during data fetch
- Per-page ErrorBoundary wrappers on all 26 data-fetching pages
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- 14 missing __init__.py files for proper Python package structure
- Comprehensive developer quick-guide (DEVELOPMENT.md)
- Release checklist and runbook (RELEASE_CHECKLIST.md)
- Dependabot configuration for automated dependency updates
- Issue templates (bug report, feature request)
- Pull request template
- Security headers: COOP, COEP, CORP, X-Permitted-Cross-Domain-Policies
- Graceful shutdown with proper shutdown logging

### Fixed
- RBAC bypass in campaign update, AB test, template endpoints
- Wrong variable bug in AB test creation (using campaign.organization_id instead of request.campaign_id)
- Missing RBAC check on set_campaign_budget endpoint
- Viewer escalation vulnerability (org update now requires admin role)
- SQLAlchemy `not` operator incorrectly used (4 instances fixed in notification_repository.py)
- Dashboard widget orphan deletion fixed
- Workflow repository UNIQUE constraint violation on save
- Auth verify_token unawaited coroutine bug
- RefreshTokenStore revoke missing in-memory fallback
- Auth logout use case missing await on RefreshTokenStore.revoke()
- Frontend TrendWidget props mismatch (accepts both data and value/label patterns)
- Frontend API base URL deduplication
- Replaced window.location.reload() with React Query refetch in multiple places
- Hardcoded mock data in analytics_routes.py replaced with real database query
- 7 N+1 query patterns resolved with batch queries
- Auth middleware singleton optimization (create verifier once, not per-request)
- Prometheus cardinality fix (path normalization replaces UUIDs/numeric IDs with {id})
- Rate limiter double-counting issue in Redis path

### Security
- Field-level encryption for email provider API keys and ad account credentials
- Security headers hardening (COOP, COEP, CORP, X-Permitted-Cross-Domain-Policies)
- Rate limit headers for client-side throttling awareness
- Removed traceback.format_exc() from error responses
- Added logging to encryption decryption fallback paths

### Changed
- Supabase JWKS now cached with 1-hour TTL
- RefreshTokenStore now Redis-backed with cross-instance revoke capability
- UsageTracker now bounded at 10,000 records with automatic eviction
- Domain now() returns timezone-aware datetimes
- Workflow transition_to raises ValidationError on invalid transitions
- ExecuteWorkflowUseCase raises EntityNotFoundError instead of returning error dict

### Performance
- 7 N+1 query patterns resolved (single batch queries replace per-row queries)
- Auth middleware now creates verifier instances once, not per-request
- UsageTracker bounded at 10,000 records

### Documentation
- OpenAPI/Swagger summaries added to all 186 route endpoints
- Return type annotations added to all ~189 route handler functions
- 99 B904 errors fixed (added `from None` to raise inside except blocks)
- Comprehensive developer documentation
- Release process documentation

### Internal
- 258 stale .cover files removed
- 2 dead helper functions removed (ok(), paginated() in schemas/common.py)
- All 1089 tests passing (0 failures)
- 60+ FK constraints with CASCADE/SET NULL
- 4 unique constraints added
- 8 composite indexes for query performance