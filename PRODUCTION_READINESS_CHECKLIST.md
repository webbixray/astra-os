# Astra OS — Production Readiness Checklist

**Version:** 1.0 | **Date:** 2025-01-14 | **Owner:** Platform Team | **Review Cadence:** Monthly

---

## Executive Sign-Off Required

| Role | Name | Signature | Date |
|------|------|-----------|------|
| CTO | | | |
| CISO | | | |
| VP Engineering | | | |
| VP Platform | | | |
| Compliance Officer | | | |

---

## 1. Infrastructure & Deployment

### Kubernetes Cluster

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Cluster version ≥ 1.28 | ☐ | `kubectl version` | Platform |
| Node pool: 3 AZs, ≥ 3 nodes/AZ | ☐ | `kubectl get nodes -o wide` | Platform |
| Node OS: Bottlerok/Ubuntu 22.04 (hardened) | ☐ | Node image audit | Platform |
| PodSecurityPolicy / PSS: Restricted | ☐ | `kubectl get psp` / `ns labels` | Platform |
| Network policies: Default deny + explicit allow | ☐ | `kubectl get netpol -A` | Platform |
| Resource quotas + LimitRanges per namespace | ☐ | `kubectl get quota,limits -A` | Platform |
| PriorityClasses defined (system > platform > app) | ☐ | `kubectl get priorityclass` | Platform |
| PodDisruptionBudgets for all deployments | ☐ | `kubectl get pdb -A` | Platform |
| TopologySpreadConstraints for HA | ☐ | Deployment spec review | Platform |

### GitOps / ArgoCD

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| ArgoCD installed, HA mode | ☐ | `kubectl get pods -n argocd` | Platform |
| Apps synced from `k8s/overlays/production` | ☐ | ArgoCD UI / `argocd app list` | Platform |
| Automated sync + prune + self-heal enabled | ☐ | App spec review | Platform |
| Drift detection alerts configured | ☐ | PrometheusRule exists | Platform |
| Secrets managed via External Secrets Operator | ☐ | `kubectl get externalsecret -A` | Platform |
| No plaintext secrets in Git | ☐ | TruffleHog scan clean | Security |

### Image Supply Chain

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Images built from distroless/gcr.io/distroless | ☐ | Dockerfile review | Platform |
| Base images scanned weekly (Trivy) | ☐ | Trivy cronjob logs | Security |
| Images signed with Cosign (keyless) | ☐ | `cosign verify` | Platform |
| SBOM generated (Syft) + attached to image | ☐ | `syft packages` | Platform |
| Admission controller verifies signatures | ☐ | Kyverno `verifyImages` policy | Platform |
| Only approved registries (ghcr.io, gcr.io) | ☐ | Kyverno `restrict-image-registries` | Platform |
| No `:latest` tags in production | ☐ | Image tag audit | Platform |

---

## 2. Security & Compliance

### Identity & Access

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| RBAC: Least privilege for all service accounts | ☐ | `kubectl auth can-i --list` | Platform |
| OIDC integration (Okta/Azure AD) for cluster access | ☐ | `kubectl config view` | Platform |
| Break-glass admin procedure documented | ☐ | Runbook exists | Security |
| Just-in-time access for production | ☐ | Teleport/Teleport/HashiCorp Boundary | Security |
| Audit logging: All kubectl commands logged | ☐ | Audit policy + Loki query | Security |

### Network Security

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| mTLS: Linkerd/Istio enabled, strict mode | ☐ | `linkerd check` / `istioctl analyze` | Platform |
| Ingress: WAF (ModSecurity + OWASP CRS) | ☐ | Ingress config + WAF logs | Security |
| Egress: Default deny, explicit allowlists | ☐ | NetworkPolicy + Cilium/Calico | Platform |
| Private endpoints for all managed services | ☐ | No public IPs on PG/Redis/ES | Platform |
| VPC flow logs enabled + retained 90 days | ☐ | Cloud provider config | Security |

### Data Protection

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Encryption at rest: PG, Redis, ES, S3 | ☐ | Cloud provider encryption config | Platform |
| Encryption in transit: TLS 1.3 everywhere | ☐ | `openssl s_client` tests | Security |
| Field-level encryption for PII (app-level) | ☐ | Code review + schema | Engineering |
| Key management: Cloud KMS / Vault | ☐ | Key rotation policy | Security |
| Key rotation: Automated, 90-day max | ☐ | Rotation job logs | Security |
| Backup encryption + tested restore (monthly) | ☐ | Restore test logs | Platform |

### Compliance Evidence

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| SOC2 Type II: Evidence collection automated | ☐ | `astra compliance export --framework SOC2` | Compliance |
| PCI DSS: Scope documented, ASV scan quarterly | ☐ | ASV report | Compliance |
| GDPR: DPA signed, DSAR workflow tested | ☐ | DSAR runbook + test | Legal |
| HIPAA (if applicable): BAA signed, audit logs | ☐ | BAA + audit log sample | Legal |
| Data retention policy enforced (RLS + TTL) | ☐ | PG partition + cron job | Engineering |

---

## 3. Observability

### Metrics (Prometheus + Grafana)

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Prometheus HA (2+ replicas, remote write) | ☐ | `kubectl get prometheus -A` | Platform |
| Retention: 15d hot, 13mo cold (Thanos/GCS) | ☐ | Prometheus config | Platform |
| All SLIs instrumented (latency, error, throughput, saturation) | ☐ | Dashboard audit | Engineering |
| SLO dashboards + burn-rate alerts (fast/medium/slow) | ☐ | `slo-burn-rate.yml` rules firing | Platform |
| Cardinality controlled (< 100k active series) | ☐ | Prometheus TSDB stats | Platform |
| Cost metrics per team/service/environment | ☐ | Cost dashboard | FinOps |

### Logging (Loki + Grafana)

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Loki HA (3+ replicas, S3 storage) | ☐ | `kubectl get loki -A` | Platform |
| Structured JSON logging (all services) | ☐ | Sample log query | Engineering |
| Correlation IDs propagated (traceparent) | ☐ | Log query with trace_id | Engineering |
| Retention: 30d hot, 1yr archive (S3) | ☐ | Loki config | Platform |
| PII redaction in logs (log / masking | ☐ | Log sample audit | Security |
| Log-based metrics for error rates | ☐ | LogQL rules | Platform |

### Tracing (Tempo + Grafana)

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Tempo HA (3+ replicas, S3) | ☐ | `kubectl get tempo -A` | Platform |
| Sampling: 10% default, 100% errors | ☐ | OTel collector config | Engineering |
| All services auto-instrumented (OTel) | ☐ | Service map in Grafana | Engineering |
| Trace-to-logs correlation working | ☐ | Trace → logs jump | Engineering |
| Retention: 7d hot, 30d archive | ☐ | Tempo config | Platform |

### Alerting (Alertmanager + PagerDuty)

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| No paging alerts for warnings | ☐ | Alert rules audit | Platform |
| All pages have runbooks linked | ☐ | Alert annotation `runbook_url` | Platform |
| Alert grouping + inhibition configured | ☐ | Alertmanager config | Platform |
| On-call rotation configured (PD/Opsgenie) | ☐ | On-call schedule | Platform |
| Notification channels: PD + Slack + Email | ☐ | Alertmanager receivers | Platform |
| Alert fatigue review (monthly) | ☐ | Review meeting notes | Platform |

---

## 4. Reliability & Resilience

### Service Level Objectives

| Service | SLI | SLO | Burn Rate Alerts | Status |
|---------|-----|-----|------------------|--------|
| API Gateway | Availability | 99.9% | 2%/5min, 5%/1h, 10%/6h | ☐ |
| API Gateway | Latency p99 < 500ms | 99% | Same | ☐ |
| Agent Orchestrator | Availability | 99.9% | Same | ☐ |
| Agent Orchestrator | Run success rate | 99.5% | Same | ☐ |
| Model Router | Availability | 99.9% | Same | ☐ |
| Model Router | Fallback rate < 5% | 99% | Same | ☐ |
| PostgreSQL | Availability | 99.95% | Same | ☐ |
| Redis | Availability | 99.95% | Same | ☐ |

### Circuit Breakers & Bulkheads

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Model Router: CB per provider (5 failures, 30s timeout) | ☐ | `resilience.py` config | Engineering |
| Agent Orchestrator: CB per downstream service | ☐ | Code review | Engineering |
| Bulkhead: Agent pools isolated by org | ☐ | K8s namespace + resource quota | Platform |
| Rate limiting: Per-org, per-endpoint | ☐ | API Gateway config | Engineering |
| Timeout budgets: 30s API, 60s agent run, 120s workflow | ☐ | Config audit | Engineering |

### Dead Letter Queues

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Redis Streams DLQ for failed agent tasks | ☐ | `dlq.py` + consumer group | Engineering |
| DLQ replay capability (CLI + API) | ☐ | `astra dlq replay` tested | Engineering |
| DLQ depth alert (> 100 messages) | ☐ | PrometheusRule | Platform |
| DLQ retention: 14 days | ☐ | Stream config | Platform |
| Failed task autopsy process documented | ☐ | Runbook | Engineering |

### Chaos Engineering

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| LitmusChaos / Chaos Mesh installed | ☐ | `kubectl get chaosengine` | Platform |
| 10 experiments defined (pod kill, latency, partition, CPU, memory, DNS, time, disk, IO, network corruption) | ☐ | Experiment manifests | Platform |
| Monthly chaos experiment scheduled | ☐ | Calendar invite | Platform |
| Experiment results documented + acted on | ☐ | Post-mortem docs | Platform |
| Blast radius controlled (namespace-scoped SA) | ☐ | RBAC review | Security |

---

## 5. Disaster Recovery

### Backup & Restore

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| PostgreSQL: PITR enabled, 35-day retention | ☐ | PG config + WAL-G | Platform |
| Redis: AOF + RDB, cross-region replica | ☐ | Redis config | Platform |
| Elasticsearch: Snapshot policy (daily, 30d retention) | ☐ | SLM policy | Platform |
| Kubernetes: Velero (daily, 30d, cross-region) | ☐ | Velero schedule + backup | Platform |
| **Restore tested monthly (documented)** | ☐ | **Restore test log** | Platform |
| RPO ≤ 1 hour, RTO ≤ 4 hours (validated) | ☐ | Test results | Platform |

### Failover

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Multi-region deployment (active-passive) | ☐ | Cluster in 2 regions | Platform |
| DNS failover (Route53/Cloudflare health checks) | ☐ | DNS config | Platform |
| Database cross-region replica (sync/async) | ☐ | PG replica status | Platform |
| Failover runbook tested quarterly | ☐ | DR test log | Platform |
| Data consistency verified post-failover | ☐ | Checksum validation | Engineering |

---

## 6. Operations

### On-Call

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Primary + secondary rotation (weekly) | ☐ | PagerDuty schedule | Platform |
| Escalation policy: 5min → 15min → 30min | ☐ | Escalation policy | Platform |
| Runbooks for all paging alerts | ☐ | Runbook repo + links in alerts | Engineering |
| Runbooks tested in last 90 days | ☐ | Test log | Engineering |
| Post-incident process: Blameless, < 48h | ☐ | Post-mortem template + examples | Engineering |

### Capacity Planning

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| CPU/Memory/Storage trends (30d, 90d) | ☐ | Grafana dashboard | Platform |
| Predictive scaling (KEDA + HPA) configured | ☐ | ScaledObject specs | Platform |
| Cost per 1k runs tracked + forecasted | ☐ | Cost dashboard | FinOps |
| Headroom: ≥ 30% CPU/mem at peak | ☐ | Capacity dashboard | Platform |
| Annual capacity review with finance | ☐ | Calendar invite | Platform |

### Change Management

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| All changes via PR + ArgoCD sync | ☐ | ArgoCD history | Platform |
| Canary deployments (10% → 50% → 100%) | ☐ | Rollout strategy | Platform |
| Automated rollback on SLO breach | ☐ | ArgoCD analysis + Prometheus | Platform |
| Database migrations: backward compatible, tested | ☐ | Migration checklist | Engineering |
| Feature flags for risky changes | ☐ | LaunchDarkly/Unleash config | Engineering |

---

## 7. Cost Management

| Check | Status | Evidence | Owner |
|-------|--------|----------|-------|
| Cost allocation tags on all resources | ☐ | Tag audit | FinOps |
| Daily cost anomaly detection | ☐ | Cloud provider / Cloudability | FinOps |
| Cost per 1k agent runs tracked | ☐ | Cost dashboard | FinOps |
| Commitment utilization > 80% (RI/Savings Plans) | ☐ | Utilization report | FinOps |
| Idle resource cleanup (daily cron) | ☐ | Cleanup job logs | Platform |
| Quarterly business review with engineering | ☐ | QBR deck | FinOps |

---

## 8. Documentation

| Document | Status | Location | Owner |
|----------|--------|----------|-------|
| Architecture Decision Records (ADRs) | ☐ | `/docs/adr/` | Engineering |
| API Reference (OpenAPI) | ☐ | `/docs/api/` | Engineering |
| Runbooks (all paging alerts) | ☐ | `/runbooks/` | Engineering |
| Incident Response Plan | ☐ | `/docs/incident-response.md` | Platform |
| Disaster Recovery Plan | ☐ | `/docs/disaster-recovery.md` | Platform |
| Security Incident Response | ☐ | `/docs/security-incident.md` | Security |
| Onboarding Guide (new engineer) | ☐ | `/docs/onboarding.md` | Engineering |
| Compliance Evidence Guide | ☐ | `/docs/compliance-evidence.md` | Compliance |

---

## 9. Final Gates

### Pre-Launch (Must Pass All)

| Gate | Criteria | Status | Sign-Off |
|------|----------|--------|----------|
| **Security** | All Critical/High vulns resolved, pen test passed | ☐ | CISO |
| **Reliability** | Load test: 2x peak, 0 errors, SLOs met | ☐ | VP Eng |
| **Observability** | All SLIs visible, alerts tuned, runbooks linked | ☐ | VP Platform |
| **Compliance** | SOC2 evidence generation works, PCI scan clean | ☐ | Compliance |
| **Disaster Recovery** | Restore test passed (RPO/RTO met) | ☐ | VP Platform |
| **Operations** | On-call ready, runbooks tested, capacity planned | ☐ | VP Platform |
| **Cost** | Budget approved, anomalies detected, tags complete | ☐ | CFO/FinOps |

### Post-Launch (30 Days)

| Check | Target | Status |
|-------|--------|--------|
| No SEV-1 incidents | 0 | ☐ |
| SLO compliance | > 99.9% | ☐ |
| Alert noise | < 5 pages/week | ☐ |
| Cost variance | < 10% of forecast | ☐ |
| Customer satisfaction (NPS) | > 50 | ☐ |

---

## Appendix: Key Commands for Verification

```bash
# Security
trivy image ghcr.io/astra-os/api:sha-<digest>
cosign verify ghcr.io/astra-os/api:sha-<digest>
kubectl get netpol -A
kubectl auth can-i --list --as=system:serviceaccount:astra-production:api

# Observability
kubectl get prometheus,alertmanager,servicemonitor -A
curl -s http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up")'
grafana cli admin list-users

# Reliability
kubectl get pdb -A
kubectl get rollout -A
litmusctl get chaosengine -A

# Disaster Recovery
velero backup get
velero restore get
kubectl exec -it postgresql-0 -- pg_basebackup --check

# Cost
kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU:.status.capacity.cpu,MEM:.status.capacity.memory
```

---

**Checklist Complete:** ☐ **Date:** ___________ **Reviewer:** ___________