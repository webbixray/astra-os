# ASTRA OS — SOC2 Type II Controls Documentation

**Version**: 1.0
**Status**: Draft — Control Framework for SOC2 Type II Readiness
**Effective Date**: 2026-07-12
**Owner**: Security Architect

---

## 1. Overview

This document catalogs the SOC2 Type II controls implemented in ASTRA OS, organized by Trust Services Criteria (TSC). Each control maps to a specific implementation in the codebase.

### Trust Services Criteria
- **CC6** — Logical and Physical Access Controls
- **CC7** — System Operations
- **CC8** — Change Management
- **CC9** — Risk Mitigation

---

## 2. Access Controls (CC6)

### CC6.1 — Logical Access Security

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Authentication via Supabase Auth | `apps/api/app/presentation/middleware/auth.py` — JWT validation middleware | Auth middleware tests, Supabase config |
| RBAC enforcement | `apps/api/app/presentation/middleware/rbac.py` — Casbin-based role checks | RBAC middleware tests |
| Multi-tenant isolation | PostgreSQL RLS policies (migration 0026) | `0026_enable_rls.py`, RLS policy tests |
| Session management | JWT with expiry, refresh token rotation | Supabase Auth config |

### CC6.2 — User Provisioning

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Organization invitations | `OrgInvitationModel` — email-based invites with role assignment | Migration 0014, invitation repository |
| Team member management | `TeamMemberRepositoryImpl` — CRUD with role-based access | Team routes, member repository |
| User deactivation | Account status management in Supabase Auth | Auth adapter |

### CC6.3 — Access Reviews

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Audit log for access | `audit_logs` table (migration 0024) — every access event logged | Audit log model, export endpoint |
| Access review queries | Governance audit routes — `/governance/audit/export` | Audit enhancement service |

---

## 3. System Operations (CC7)

### CC7.1 — Detection of Unauthorized Activities

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Agent action audit trail | `agent_actions` table — every agent action recorded with reasoning trace | Migration 0029, AgentAction model |
| Tamper-evident audit log | SHA-256 hash chain in AuditEnhancementService | `audit_enhancement.py` — `verify_chain()` |
| Domain event logging | EventBus — all mutations emit domain events | `event_bus.py` — event history |

### CC7.2 — Monitoring

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Structured logging | JSON-formatted logs via Python logging | Application logger configuration |
| Health checks | `/health` and `/health/ready` endpoints | `health.py` routes |
| Metrics | Prometheus metrics via `app/infrastructure/metrics.py` | Metrics middleware |

### CC7.3 — Incident Response

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Error tracking | Domain exceptions with structured codes | `domain_exceptions.py` |
| Agent failure recording | `AgentAction.record_failure()` — error messages persisted | Governance test suite |

### CC7.4 — Availability

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Database connection pooling | SQLAlchemy async session factory | `dependencies.py` — `get_db()` |
| Redis for caching | Redis 7 with health checks | Docker compose, connection management |
| Health check endpoints | Liveness and readiness probes | K8s deployment config |

---

## 4. Change Management (CC8)

### CC8.1 — Change Authorization

| Control | Implementation | Evidence |
|---------|---------------|----------|
| GitFlow branching | Protected `main` branch, PR required | `ENGINEERING_CONSTITUTION.md` Article III |
| PR review requirements | 2 approvals required (1 domain owner, 1 ARB for architectural) | PR template |
| CI/CD gates | All 10 pipeline stages must pass | `.github/workflows/ci.yml` |

### CC8.2 — Change Testing

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Unit tests | ≥80% line coverage, ≥70% branch coverage | pytest + vitest, 340+ tests |
| Integration tests | Critical path coverage | `test_m2_integration.py`, `test_governance.py` |
| E2E tests | Critical user journeys | Playwright (planned for M6) |
| Security scanning | SAST + dependency audit | bandit, trivy, semgrep in CI |

### CC8.3 — Change Deployment

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Database migrations | Alembic — versioned, reversible | `alembic/versions/` — 29 migrations |
| Container deployment | Multi-stage Docker + K8s | `docker/`, `k8s/` |
| Rollback capability | Migration downgrade functions | Every migration has `downgrade()` |

---

## 5. Risk Mitigation (CC9)

### CC9.1 — Risk Assessment

| Control | Implementation | Evidence |
|---------|---------------|----------|
| AI autonomy levels | 3-tier system (Advisory/Semi-Auto/Full-Auto) | `autonomy.py` — AutonomyConfig |
| Approval gates | Configurable rules for spend, brand, audience | `approval.py` — ApprovalRule |
| Spend limits | Auto-approve caps per action type | `AutonomyConfig.auto_approve_spend_limit` |

### CC9.2 — Data Classification

| Control | Implementation | Evidence |
|---------|---------------|----------|
| PII handling | Audit export strips PII when `include_pii=False` | `AuditEnhancementService.export_entries()` |
| Secrets management | Never in repo, vault-based | `SECURITY.md`, `.env.example` |
| Data retention | 7-year audit log retention policy | `AuditEnhancementService.get_retention_cutoff()` |

### CC9.3 — Vendor Management

| Control | Implementation | Evidence |
|---------|---------------|----------|
| AI model fallback chain | NVIDIA NIM → OpenAI → Anthropic → Gemini | `router.py` — ModelRouterFacade |
| Ad platform adapters | Abstracted via ports, contract tests | `ports/ad_platform_port.py` |
| Infrastructure dependencies | Docker Compose for local, K8s for production | `docker-compose.yml`, `k8s/` |

---

## 6. AI-Specific Controls (ASTRA-specific)

| Control | Implementation | Evidence |
|---------|---------------|----------|
| Explainability | Every agent decision has reasoning trace | `explainability.py` — `to_explanation()` |
| Human-in-the-loop | Approval required for high-risk actions | `autonomy_enforcement.py` |
| Audit trail | Agent actions stored with reasoning, cost, model | `agent_actions` table |
| Tamper evidence | SHA-256 hash chain on audit entries | `AuditEnhancementService` |
| Cost tracking | Token usage and cost per action | `AgentAction.tokens_used`, `cost_usd` |

---

## 7. Evidence Collection Checklist

For SOC2 Type II audit, collect evidence for:

- [ ] Access control policies (documented)
- [ ] User provisioning/deprovisioning records
- [ ] Audit log exports (90-day sample)
- [ ] Change management records (PRs, approvals, CI results)
- [ ] Incident response records
- [ ] Risk assessment documentation
- [ ] Vendor security assessments
- [ ] Data retention compliance records
- [ ] AI governance audit trail
- [ ] Penetration test results
- [ ] Vulnerability scan reports

---

## 8. Compliance Readiness Score

| Domain | Status | Notes |
|--------|--------|-------|
| Access Controls | 🟡 70% | Auth/RBAC working, need formal access review process |
| System Operations | 🟡 65% | Logging/monitoring in place, need SLO dashboards |
| Change Management | 🟢 85% | CI/CD, PR reviews, testing all working |
| Risk Mitigation | 🟢 80% | AI governance strong, need formal risk register |
| Documentation | 🟡 60% | Constitution, architecture, task specs — need runbooks |

**Overall Readiness**: ~72% — Needs targeted work on formal policies, access reviews, and runbooks for full SOC2 Type II.

---

**End of SOC2 Controls Document**

*This is a living document. Updated as controls are implemented or audited.*
