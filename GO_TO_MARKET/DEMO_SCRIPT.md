# Astra OS — 15-Minute Compliance Demo Script

## Demo Principles

1. **Show, don't tell** — Every claim backed by live UI/CLI
2. **Compliance-first narrative** — Every feature maps to audit requirement
3. **15 minutes max** — Respect the compliance officer's time
4. **End with evidence** — Leave them with the export file

---

## Pre-Demo Setup (5 min before call)

```bash
# 1. Start demo org (pre-seeded)
astra auth login --org demo-fintech-compliance
astra config set demo.mode true

# 2. Verify pre-loaded assets
astra agents list --org demo-fintech-compliance
# Should show: CEO, Content Specialist, Compliance Reviewer, Shadow Comparator

# 3. Verify shadow mode session ready
astra shadow sessions list --status pending
# Should show: "Blog Post: Q3 Fintech Compliance Trends" — pending review
```

---

## Demo Flow (15 Minutes)

### 0:00–1:00 | Hook: The Problem (1 min)
> **"Before we dive in — quick question: When your auditor asks 'show me who approved this AI-generated blog post that mentioned customer PII,' what do you show them?"**
>
> *Pause. Let them answer. Usually: "We don't use AI" or "We have a spreadsheet" or "Good question."*
>
> **"That's why we built Astra OS. In the next 14 minutes, I'll show you how a fintech marketing team generates compliant content — with every decision logged, every output approved, and audit evidence exported in one click."**

---

### 1:00–4:00 | Shadow Mode Live: AI vs Human (3 min)

**Action:** Show the pending shadow session
```bash
astra shadow sessions get "blog-q3-fintech-trends" --format rich
```

**UI Shows:**
```
┌─────────────────────────────────────────────────────────────┐
│ SHADOW SESSION: blog-q3-fintech-trends                      │
├─────────────────────────────────────────────────────────────┤
│ Topic: "Q3 Fintech Compliance Trends for Blog"              │
│ Status: PENDING_REVIEW                                      │
│ Created: 2025-01-14 10:23 UTC                               │
│ Agent: content-specialist-v2                                │
├─────────────────────────────────────────────────────────────┤
│ AI OUTPUT (shadow)                                          │
│ ─────────────────────────────────────────────────────────── │
│ "Fintechs in 2025 face evolving regulatory landscapes...    │
│  The CFPB's new rule 1033 mandates open banking APIs...     │
│  Customer data portability is now a competitive advantage." │
├─────────────────────────────────────────────────────────────┤
│ HUMAN REVIEWER: sarah.chen@compliance.fintech.com           │
│ Status: NOT_REVIEWED                                        │
│ SLA: 4 hours remaining                                      │
├─────────────────────────────────────────────────────────────┤
│ DIFF ANALYSIS                                               │
│ ─────────────────────────────────────────────────────────── │
│ ✅ No PII detected                                          │
│ ⚠️  Mentions "Rule 1033" — requires legal citation check    │
│ ✅ No financial advice language                             │
│ ✅ Brand voice: 94% match                                   │
└─────────────────────────────────────────────────────────────┘
```

**Narrate:**
> **"This is shadow mode. The AI wrote this blog post in parallel. It never published. It sits here until a human reviews it. Notice: the system flagged 'Rule 1033' as needing legal citation — that's our custom policy engine catching regulatory references. No PII, no financial advice, 94% brand voice match. This is what your compliance team reviews — not raw AI output."**

---

### 4:00–7:00 | Approval Chain in Action (3 min)

**Action:** Approve via Slack (show notification) OR CLI
```bash
# Simulate approval
astra shadow sessions approve "blog-q3-fintech-trends" \
  --reviewer sarah.chen@compliance.fintech.com \
  --decision APPROVED \
  --notes "Rule 1033 citation added: CFPB-2024-0033. Approved for publish."
```

**Show result:**
```
✅ Session APPROVED
Reviewer: sarah.chen@compliance.fintech.com
Decision: APPROVED
Timestamp: 2025-01-14 10:27 UTC
Notes: Rule 1033 citation added: CFPB-2024-0033. Approved for publish.
Next: Content published to CMS via webhook
```

**Narrate:**
> **"Approval happened in Slack — Sarah got a notification, clicked 'Approve,' added the citation. Done. Every approval is logged with who, when, what, and why. No email chains, no lost context. This *is* your audit trail."**

---

### 7:00–10:00 | Immutable Audit Trail (3 min)

**Action:** Show the full audit log
```bash
astra audit get "blog-q3-fintech-trends" --format timeline
```

**Shows:**
```
┌────────────────────────────────────────────────────────────────┐
│ AUDIT TRAIL: blog-q3-fintech-trends                           │
├──────────────┬─────────────────────┬──────────────────────────┤
│ TIMESTAMP    │ ACTOR               │ ACTION                   │
├──────────────┼─────────────────────┼──────────────────────────┤
│ 10:23:12     │ content-specialist  │ AI_GENERATED (shadow)    │
│              │                     │ model: gpt-4o            │
│              │                     │ tokens: 1,247            │
│              │                     │ cost: $0.018             │
├──────────────┼─────────────────────┼──────────────────────────┤
│ 10:23:15     │ policy-engine       │ PII_SCAN: PASS           │
│              │                     │ REGULATORY_FLAG: 1033    │
│              │                     │ BRAND_VOICE: 94%         │
├──────────────┼─────────────────────┼──────────────────────────┤
│ 10:27:03     │ sarah.chen@comp...  │ HUMAN_REVIEW: APPROVED   │
│              │                     │ NOTES: Citation added    │
├──────────────┼─────────────────────┼──────────────────────────┤
│ 10:27:05     │ publisher-agent     │ PUBLISHED: CMS_WEBHOOK   │
│              │                     │ URL: blog.fintech.com/.. │
└──────────────┴─────────────────────┴──────────────────────────┘
```

**Narrate:**
> **"Immutable. Tamper-evident. Every AI decision, every policy check, every human action — cryptographically linked. Your auditor doesn't need to trust you; they verify the chain. This is what 'provable compliance' looks like."**

---

### 10:00–12:00 | Model Router + Cost Governance (2 min)

**Action:**
```bash
astra model-router stats --org demo-fintech-compliance --last 24h
astra costs report --org demo-fintech-compliance --period 30d --format table
```

**Shows:**
```
MODEL ROUTER STATS (24h)
┌──────────────┬────────┬──────────┬────────────┬─────────────┐
│ Provider     │ Calls  │ Success  │ Avg Latency│ Cost        │
├──────────────┼────────┼──────────┼────────────┼─────────────┤
│ NVIDIA NIM   │ 1,247  │ 99.2%    │ 312ms      │ $0.00 (local)│
│ OpenAI       │ 234    │ 98.7%    │ 1.2s       │ $12.47      │
│ Anthropic    │ 89     │ 100%     │ 2.1s       │ $8.92       │
│ Gemini       │ 12     │ 100%     │ 890ms      │ $0.34       │
└──────────────┴────────┴──────────┴────────────┴─────────────┘
Fallback rate: 18% → saved $247 vs pure OpenAI

COST REPORT (30d)
┌──────────────────┬───────────┬────────────┐
│ Category         │ Runs      │ Cost       │
├──────────────────┼───────────┼────────────┤
│ Content Gen      │ 4,231     │ $187.42    │
│ Compliance Check │ 4,231     │ $0.00      │
│ Shadow Compare   │ 4,231     │ $12.18     │
│ Approval Chains  │ 4,231     │ $0.00      │
├──────────────────┼───────────┼────────────┤
│ TOTAL            │           │ $199.60    │
│ BUDGET           │           │ $500.00    │
│ UTILIZATION      │           │ 40%        │
└──────────────────┴───────────┴────────────┘
```

**Narrate:**
> **"Smart routing: NVIDIA NIM handles 85% locally (zero cost). OpenAI/Anthropic only for complex reasoning. Fallback chain means zero downtime. Budget guardrails auto-pause at 80% — no surprise bills. This is $200/month for 4,000 compliant runs. Compare to $2,000+ on pure OpenAI."**

---

### 12:00–14:00 | One-Click Compliance Export (2 min)

**Action:**
```bash
astra compliance export --org demo-fintech-compliance \
  --framework SOC2 \
  --period "2025-01-01 to 2025-01-31" \
  --output soc2-evidence-jan2025.zip
```

**Show the generated files:**
```
soc2-evidence-jan2025.zip
├── evidence/
│   ├── CC6.1_access_control.csv          # All approvals with timestamps
│   ├── CC7.2_system_monitoring.csv       # All AI runs + policy checks
│   ├── CC8.1_change_management.csv       # Model router changes
│   └── CC9.1_risk_mitigation.csv         # Shadow mode rejections
├── attestation/
│   └── compliance_officer_attestation.pdf # Signed by your CCO
└── README.md                              # Auditor instructions
```

**Narrate:**
> **"One command. SOC2 evidence package. CC6.1, CC7.2, CC8.1, CC9.1 — all mapped. Your compliance officer signs the attestation. Auditor downloads, verifies, moves on. What used to take 2 weeks now takes 2 minutes."**

---

### 14:00–15:00 | Close + Next Steps (1 min)

> **"Here's what we just proved:**
> - ✅ AI content generated **safely** (shadow mode)
> - ✅ Every decision **approved by human** (approval chain)
> - ✅ Every action **logged immutably** (audit trail)
> - ✅ Costs **controlled & optimized** (model router)
> - ✅ Audit evidence **exported in one click** (compliance export)
>
> **This is why [Fintech Customer] chose us. They went from 'legal blocks AI' to '4,000 compliant runs/month' in 3 weeks.**
>
> **Next step: Let's run a 30-day pilot with your team. You pick 2 content types. We deploy in your VPC. Your compliance team owns the approval chains. If it doesn't pass your internal audit, you pay nothing.**
>
> **Shall we set that up?"**

---

## Demo Variants

### For Technical Buyers (CTO/VP Eng) — Add 5 min
- Show Kubernetes deployment: `kubectl get pods -n astra-production`
- Show RLS policy: `kubectl exec -it postgresql -- psql -c "SELECT * FROM pg_policies WHERE tablename='audit_logs';"`
- Show OTel traces in Tempo: "Every agent run is a trace"

### For CFO — Add 3 min
- Show cost comparison slide: "Pure OpenAI: $2,400/mo → Astra OS: $199/mo"
- Show budget guardrails: "Auto-pause at 80%, hard stop at 100%"
- Show ROI: "4,000 runs × 30 min saved = 2,000 hrs/mo = $150k+ value"

### For Compliance Officer (Deep Dive) — Add 10 min
- Show custom policy DSL: `policy "no-pii" { deny if contains(pii) }`
- Show rejection examples: `astra shadow sessions list --decision REJECTED`
- Show retention config: `astra config get audit.retention_years`

---

## Demo Environment Checklist

| Item | Status | Notes |
|------|--------|-------|
| Demo org created | ☐ | `astra auth login --org demo-fintech-compliance` |
| Agents seeded | ☐ | CEO, Content Specialist, Compliance Reviewer, Shadow Comparator |
| Shadow session ready | ☐ | "blog-q3-fintech-trends" pending |
| Approval chain configured | ☐ | sarah.chen@compliance.fintech.com |
| Model router active | ☐ | NIM + OpenAI + Anthropic + Gemini |
| Budget set | ☐ | $500/mo, 80% alert |
| Compliance export tested | ☐ | SOC2 + PCI frameworks |
| Slack webhook connected | ☐ | #compliance-approvals channel |
| Demo script rehearsed | ☐ | <15 min with timer |

---

## Objection Cards (Keep Handy)

| Objection | Response |
|-----------|----------|
| "We need HubSpot integration" | "Built-in. 2-week implementation. Show me your workflow." |
| "We use Azure OpenAI" | "Supported. Private endpoint, your keys, your VPC." |
| "We need 100k runs/month" | "Professional tier = 100k. Enterprise = unlimited." |
| "Our legal team is slow" | "That's why shadow mode exists — they review at their pace, AI runs in parallel." |
| "We're not fintech" | "Same architecture works for healthtech (HIPAA), insurtech (state regs), SaaS (SOC2)." |
| "Price is high" | "Writer Enterprise = $20k/yr for partial compliance. We're $120k/yr for *complete* compliance + orchestration." |
