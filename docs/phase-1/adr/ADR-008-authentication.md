# ADR-008: JWT + OAuth/OIDC with Supabase Auth or Auth0

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Security Engineer, Infrastructure Architect

## Context

ASTRA OS requires authentication for organizations, teams, and users. Needs to support email/password, social login (Google, GitHub, Microsoft), SSO/SAML for enterprise, API key auth for programmatic access, and MFA.

## Decision

Use **Supabase Auth** for initial implementation (cost-effective, built-in PostgreSQL integration), with migration path to Auth0 for enterprise SSO requirements.

### Authentication Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│   Browser    │────▶│  Next.js      │────▶│  FastAPI  │
│              │     │  (Auth proxy) │     │  (Verify) │
└─────────────┘     └──────┬───────┘     └────┬─────┘
                           │                  │
                           ▼                  ▼
                    ┌──────────────┐     ┌──────────┐
                    │ Supabase Auth │     │ PostgreSQL│
                    │ (JWT issuer)  │     │ (Users)   │
                    └──────────────┘     └──────────┘
```

### Token Strategy

| Token | Type | Lifetime | Purpose |
|---|---|---|---|
| **Access Token** | JWT | 15 min | API authentication |
| **Refresh Token** | Opaque | 7 days | Session persistence |
| **API Key** | HMAC | Custom | Programmatic access |
| **Impersonation** | JWT | 1 hour | Admin support |

### RBAC Model

```
Organization
├── Owner (full access)
├── Admin (manage teams, billing)
├── Member (feature access based on roles)
│   ├── Marketing Manager
│   ├── Content Creator
│   ├── Analyst
│   └── Viewer

Role → Permissions (resource:action)
Example: campaign:create, campaign:approve, analytics:read
```

## Rationale

1. **Supabase Auth** is cost-effective for v1 and integrates directly with PostgreSQL
2. **JWT** enables stateless API validation (FastAPI verifies without DB lookup)
3. **API keys** needed for workflow automation and third-party integrations
4. **RBAC at the application layer** rather than database layer for fine-grained control

## Consequences

- Supabase Auth limits enterprise SSO — upgrade to Auth0/PingIdentity when enterprise customers require SAML
- JWT revocation requires a blacklist or short expiry
- API key rotation and hashing needed for security
- Audit logging for all authentication events required

## Alternatives Considered

- **Auth0**: Best enterprise SSO support but expensive at scale
- **Clerk**: Great DX but data residency concerns
- **Firebase Auth**: Google lock-in, poor enterprise SSO
- **Custom auth**: Too much security surface area to build from scratch
