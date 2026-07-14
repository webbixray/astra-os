# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Yes             |
| < 0.1   | ❌ No              |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities by:

1. **Email**: security@astra-os.io (preferred)
2. **GitHub Security Advisories**: Use the "Report a vulnerability" button on the GitHub Security tab
3. **Encrypted**: Our PGP key is available at https://astra-os.io/security/pgp-key.asc

### What to Include

Please provide as much of the following information as possible:

- Type of vulnerability (e.g., RCE, SQLi, XSS, Auth bypass, etc.)
- Affected component(s) and version(s)
- Steps to reproduce or proof-of-concept
- Potential impact assessment
- Suggested fix or mitigation (if known)

### Response Timeline

| Severity | Initial Response | Fix Target |
| -------- | ---------------- | ---------- |
| Critical | 24 hours         | 7 days     |
| High     | 48 hours         | 14 days    |
| Medium   | 5 business days  | 30 days    |
| Low      | 10 business days | 90 days    |

We will:
1. Acknowledge receipt within the initial response window
2. Validate and reproduce the issue
3. Develop and test a fix
4. Coordinate disclosure timeline with you
5. Release the fix and publish a security advisory

## Security Best Practices

### For Users

- Always use the latest stable release
- Keep dependencies updated (enable Dependabot alerts)
- Use strong, unique passwords and enable MFA
- Rotate API keys regularly (recommended: 90 days)
- Run containers as non-root user
- Enable TLS/mTLS for all service communication
- Use secrets management (Vault, Sealed Secrets, External Secrets Operator)

### For Contributors

- Never commit secrets, API keys, or credentials
- Use `.env.example` for configuration templates
- Run security checks before committing:
  ```bash
  bandit -r .
  trufflehog --no-verification .
  pip-audit --desc
  ```
- Follow secure coding practices:
  - Parameterize all SQL queries
  - Validate and sanitize all inputs
  - Use prepared statements
  - Implement proper authentication/authorization
  - Use CSRF protection for state-changing operations
  - Set secure headers (CSP, HSTS, etc.)

## Security Architecture

### Authentication & Authorization

- JWT-based authentication with short-lived access tokens (15 min) and refresh tokens
- Role-Based Access Control (RBAC) with fine-grained permissions
- Organization-level isolation (multi-tenancy)
- API key management with scopes and expiration

### Network Security

- mTLS between all microservices (Linkerd/Istio)
- Network policies restricting pod-to-pod communication
- Ingress with WAF rules (ModSecurity)
- Egress controls for external API calls

### Data Protection

- Encryption at rest (AES-256) for databases and object storage
- Encryption in transit (TLS 1.3) for all communication
- Field-level encryption for PII
- Automated key rotation (90 days)
- Data minimization and retention policies

### Supply Chain Security

- Signed container images (cosign + keyless)
- SBOM generation (Syft) for all releases
- Dependency scanning (pip-audit, npm audit, Trivy)
- Provenance attestations (SLSA Level 3)
- Verified builds (GitHub Actions + Sigstore)

## Compliance

### Standards Alignment

- **SOC 2 Type II** - In progress
- **GDPR** - Data protection by design
- **CCPA** - Consumer privacy rights
- **ISO 27001** - Target certification

### Audit Trail

All security-relevant events are logged:
- Authentication attempts (success/failure)
- Authorization decisions
- Data access/modification
- Configuration changes
- Administrative actions

Logs are:
- Immutable (append-only)
- Tamper-evident (hash chaining)
- Retained for 7 years
- Queryable via SIEM

## Vulnerability Disclosure

### Coordinated Disclosure

We follow coordinated vulnerability disclosure:

1. Researcher reports vulnerability privately
2. We acknowledge and validate
3. We develop and test fix
4. We agree on disclosure date (typically 90 days)
5. We release fix and publish advisory
6. Credit given to researcher (if desired)

### Safe Harbor

We authorize good-faith security research including:

- Testing on staging/demo environments
- Reporting vulnerabilities via proper channels
- Not accessing/modifying user data
- Not disrupting services

We will not pursue legal action against researchers who follow this policy.

## Security Contacts

| Role | Contact |
| ---- | ------- |
| Security Team | security@astra-os.io |
| CISO | ciso@astra-os.io |
| Incident Response | incident@astra-os.io |

---

**Last Updated**: 2025-07-14
**Version**: 1.0
**Next Review**: 2025-10-14