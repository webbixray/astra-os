# Security Policy

## Supported Versions
| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ Active |
| < 1.0   | ❌ |

## Reporting a Vulnerability
Email **security@astra-os.io**. 48h response. Never file public GitHub issues.

### Include:
- Type (SQLi, XSS, priv escalation, etc.)
- Affected source location (file + line or commit)
- Reproduction steps
- Proof of concept (if possible)
- Impact assessment

## Security Architecture

| Layer | Protection |
|-------|-----------|
| Authentication | JWT with refresh rotation, session management |
| Authorization | RBAC + org-scoped permissions + Row-Level Security |
| CSRF | Double-submit cookie pattern, HMAC validation |
| Rate Limiting | Per-IP + per-user, Redis-backed, burst-aware |
| Input Validation | Pydantic strict schemas on all endpoints |
| SQL Injection | Parameterized queries via SQLAlchemy ORM |
| XSS | CSP headers + input sanitization + output encoding |
| Security Headers | HSTS, X-Frame-Options, X-Content-Type-Options, Permissions-Policy |
| Encryption at Rest | AES-256-GCM for PII / credentials |
| Encryption in Transit | TLS 1.3 required |
| Audit Logging | All security events immutable |
| Container Security | Distroless images, non-root user, read-only FS |
| Supply Chain | Cosign-signed images, SBOM generation, dependency scanning |

## CI/CD Gates
Every PR must pass: Bandit → Semgrep → TruffleHog → Trivy → Hadolint → pip-audit → npm audit → Unit + Integration tests

## Dependency Management
- Dependabot + Renovate configured for automated PRs
- Weekly full security scans (Monday 02:00 UTC)
- Critical vulns auto-create security issues
