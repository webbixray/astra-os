# Astra OS — Beachhead Packaging & Pricing

## Package Philosophy

**Not "tiers" — solutions.** Each package solves a specific compliance maturity stage.

| Package | Target Maturity | Core Problem Solved |
|---------|-----------------|---------------------|
| **Compliance Starter** | "We need AI but legal says no" | First compliant AI content workflow |
| **Compliance Professional** | "We're scaling AI across teams" | Multi-team governance + audit automation |
| **Compliance Enterprise** | "We're regulated (PCI/SOC2/HIPAA)" | Full compliance program + liability protection |

---

## Package Details

### 🟢 Compliance Starter — $3,000/mo
**Target:** Fintech Series A/B, 50–200 employees, first SOC2 audit

| Included | Limit |
|----------|-------|
| **Shadow Mode** (AI runs, human approves) | ✅ Unlimited |
| **Audit Trail** (immutable, tamper-evident) | ✅ 1 year retention |
| **Approval Chains** (1 chain, up to 3 approvers) | ✅ |
| **Agents** (CEO, Content Specialist, Compliance Reviewer) | 5 agents |
| **Runs/Month** | 10,000 |
| **Model Router** (NVIDIA NIM → OpenAI → Anthropic → Gemini) | ✅ |
| **RLS / Org Isolation** | ✅ |
| **API + CLI Access** | ✅ |
| **Slack/Teams Approval Notifications** | ✅ |
| **SOC2 Evidence Export** (manual) | ✅ |
| **SSO (SAML/OIDC)** | ❌ |
| **Custom Policies** | ❌ |
| **Dedicated Model Router** | ❌ |
| **Compliance Export Pack (SOC2/PCI/GDPR)** | ❌ |
| **SLA** | 99.5% |
| **Support** | Email (24h) |

**Overage:** $0.50/run over 10k | **Hard Cap:** 20k runs/mo

---

### 🔵 Compliance Professional — $10,000/mo
**Target:** Fintech Series B/C, 200–1,000 employees, scaling AI across marketing/growth/compliance teams

| Included | Limit |
|----------|-------|
| **Everything in Starter** | ✅ |
| **Approval Chains** | Unlimited (multi-level, conditional) |
| **Agents** | 25 agents |
| **Runs/Month** | 100,000 |
| **Custom Policies** (brand voice, regulatory rules, PII handling) | ✅ 10 policies |
| **Compliance Export Pack** (SOC2/PCI/GDPR — one-click) | ✅ |
| **Multi-Org / Multi-Workspace** | ✅ 5 orgs |
| **Advanced Cost Guardrails** (budgets, auto-pause, forecasting) | ✅ |
| **Cross-Agent Learning** (share winning patterns) | ✅ |
| **Dedicated Model Router Instance** | ✅ |
| **SSO (SAML/OIDC) + SCIM** | ✅ |
| **Audit Trail Retention** | 3 years |
| **SLA** | 99.9% |
| **Support** | Slack + Email (4h business hours) |

**Overage:** $0.30/run over 100k | **Hard Cap:** 200k runs/mo

---

### 🟣 Compliance Enterprise — $25,000+/mo
**Target:** Regulated enterprises (PCI DSS Level 1, HIPAA, GDPR, SOX), 1,000+ employees

| Included | Limit |
|----------|-------|
| **Everything in Professional** | ✅ |
| **Unlimited Agents / Runs / Orgs** | ✅ |
| **Custom Policy Engine** (DSL for regulatory rules) | ✅ Unlimited |
| **On-Prem / VPC Deployment** (your cloud, your keys) | ✅ |
| **Dedicated Model Router + Custom Models** | ✅ |
| **Compliance Export Pack** (automated, scheduled, auditor-ready) | ✅ |
| **Custom Integrations** (internal tools, legacy systems) | ✅ 3/yr included |
| **Penetration Test Results Sharing** | ✅ |
| **Audit Trail Retention** | 7 years (configurable) |
| **Private Model Endpoints** (Azure OpenAI, AWS Bedrock, GCP Vertex) | ✅ |
| **Compliance Officer Dashboard** (real-time risk view) | ✅ |
| **SLA** | 99.95% + RPO < 1hr, RTO < 4hr |
| **Support** | Dedicated CSM + 24/7 on-call + quarterly business reviews |

**Pricing:** $25,000/mo base + $0.10/run over 500k | Custom contract

---

## Packaging Rules (Non-Negotiable)

| Rule | Rationale |
|------|-----------|
| **No per-seat pricing** | Value = compliant runs, not users |
| **Hard caps enforced at orchestrator level** | Prevents bill shock, forces upgrade conversation |
| **Shadow mode included in ALL packages** | Core differentiator — never gate it |
| **Compliance export only in Professional+** | Primary upgrade lever for compliance teams |
| **SSO only in Professional+** | Enterprise buying signal |
| **No annual discount > 15%** | Protects ARR predictability; use multi-year for deeper discounts |

---

## Usage Metrics (What Counts as a "Run")

| Action | Runs Consumed |
|--------|---------------|
| Agent execution (any type) | 1 |
| Tool call (within agent) | 0 (included) |
| Delegation to sub-agent | 1 (counts as separate run) |
| Shadow mode comparison | 1 (AI run) + 0 (human review) |
| Approval chain execution | 0 (included) |
| Compliance export generation | 0 (included) |

---

## Competitive Pricing Anchor

| Vendor | Price | Compliance |
|--------|-------|------------|
| Jasper (Business) | $6,000/yr | ❌ |
| Copy.ai (Enterprise) | $12,000+/yr | ❌ |
| Writer (Enterprise) | $20,000+/yr | Partial |
| Custom Build | $500k+ upfront | ✅ (you build) |
| **Astra OS Professional** | **$120,000/yr** | **✅ Native** |

**Anchor message:** "Writer charges $20k for partial compliance. We charge $120k for *complete* compliance + orchestration + model routing + cost optimization."

---

## Discount Framework (Controlled)

| Scenario | Max Discount | Approval Required |
|----------|--------------|-------------------|
| 2-year prepaid | 15% | VP Sales |
| 3-year prepaid | 20% | CRO |
| Design Partner (6-month pilot) | 50% (first 6mo) | CEO |
| Non-profit / Education | 30% | VP Sales |
| Competitive displacement (Writer/Jasper) | 25% (year 1 only) | CRO |

**No:** Volume discounts, startup discounts, "end of quarter" discounts, partner discounts without signed agreement.

---

## Billing Implementation (Technical)

```python
# Enforced at agent_orchestrator/supervisor.py level
PACKAGE_LIMITS = {
    "starter": {"runs_per_month": 10_000, "hard_cap": 20_000, "overage_rate": 0.50},
    "professional": {"runs_per_month": 100_000, "hard_cap": 200_000, "overage_rate": 0.30},
    "enterprise": {"runs_per_month": 500_000, "hard_cap": None, "overage_rate": 0.10},
}

# Checked at start of every agent run
async def check_package_limits(org_id: UUID, package: str) -> bool:
    current = await get_monthly_runs(org_id)
    limit = PACKAGE_LIMITS[package]["runs_per_month"]
    hard_cap = PACKAGE_LIMITS[package]["hard_cap"]
    
    if hard_cap and current >= hard_cap:
        raise PackageLimitExceeded("Hard cap reached — upgrade required")
    elif current >= limit:
        # Allow overage but alert
        await alert_billing(org_id, current, limit)
    return True
```

---

## Sales Enablement: One-Pager per Package

Create 3 PDFs (1 page each):

1. **Starter:** "First compliant AI content in 48 hours"
2. **Professional:** "Scale AI across marketing — audit-ready by default"
3. **Enterprise:** "Your compliance program, automated"

Each includes: Problem → Solution → What's Included → Proof Points → Next Step