# ASTRA OS — API Reference

**Version**: 1.0
**Base URL**: `https://api.astra-os.com/api/v1`
**Authentication**: Bearer Token (JWT)
**Content-Type**: `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Organizations](#organizations)
3. [Campaigns](#campaigns)
4. [Workflows](#workflows)
5. [Agents](#agents)
6. [Knowledge & Intelligence](#knowledge--intelligence)
7. [Social Intelligence](#social-intelligence)
8. [Shadow Mode](#shadow-mode)
9. [Observability](#observability)
10. [Error Codes](#error-codes)

---

## Authentication

All API requests require a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Token Refresh

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

---

## Organizations

### Create Organization

```http
POST /organizations
Content-Type: application/json

{
  "name": "Acme Corp",
  "slug": "acme-corp"
}
```

### Get Organization

```http
GET /organizations/{organization_id}
```

### List User Organizations

```http
GET /organizations/my
```

### Update Organization

```http
PATCH /organizations/{organization_id}
Content-Type: application/json

{
  "name": "New Name",
  "settings": {
    "timezone": "America/New_York",
    "currency": "USD"
  }
}
```

---

## Campaigns

### Create Campaign

```http
POST /campaigns
Content-Type: application/json

{
  "organization_id": "uuid",
  "name": "Q4 Holiday Campaign",
  "objective": "conversions",
  "target_audience": {
    "age_min": 25,
    "age_max": 55,
    "interests": ["shopping", "technology"],
    "locations": ["US", "CA"]
  },
  "budget": 50000.00,
  "start_date": "2024-11-01",
  "end_date": "2024-12-31"
}
```

### Get Campaign

```http
GET /campaigns/{campaign_id}
```

### List Campaigns

```http
GET /campaigns?organization_id=uuid&status=active&page=1&limit=20
```

### Update Campaign

```http
PATCH /campaigns/{campaign_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "budget": 60000.00
}
```

### Launch Campaign

```http
POST /campaigns/{campaign_id}/launch
Content-Type: application/json

{
  "organization_id": "uuid"
}
```

### Pause Campaign

```http
POST /campaigns/{campaign_id}/pause
Content-Type: application/json

{
  "organization_id": "uuid"
}
```

### Get Campaign Budget

```http
GET /campaigns/{campaign_id}/budget?organization_id=uuid
```

### Set Campaign Budget

```http
POST /campaigns/{campaign_id}/budget
Content-Type: application/json

{
  "organization_id": "uuid",
  "total_budget": 10000.00,
  "daily_budget": 500.00,
  "pacing_strategy": "even"
}
```

### Get Campaign Pacing

```http
GET /campaigns/{campaign_id}/pacing?organization_id=uuid&strategy=even
```

### Record Spend

```http
POST /campaigns/{campaign_id}/spend
Content-Type: application/json

{
  "organization_id": "uuid",
  "amount_usd": 1500.00,
  "currency": "USD"
}
```

---

## Workflows

### Create Workflow

```http
POST /workflows
Content-Type: application/json

{
  "organization_id": "uuid",
  "name": "Content Approval Workflow",
  "description": "Review and approve content before publishing"
}
```

### Get Workflow

```http
GET /workflows/{workflow_id}
```

### List Workflows

```http
GET /workflows?organization_id=uuid&status=active
```

### Update Workflow

```http
PATCH /workflows/{workflow_id}
Content-Type: application/json

{
  "nodes": [...],
  "edges": [...]
}
```

### Execute Workflow

```http
POST /workflows/{workflow_id}/execute
Content-Type: application/json

{
  "organization_id": "uuid",
  "triggered_by": "uuid"
}
```

### List Executions

```http
GET /workflows/{workflow_id}/executions
```

### Workflow Templates

```http
GET /workflows/templates
GET /workflows/templates/{template_id}
POST /workflows/templates/{template_id}/instantiate
Content-Type: application/json

{
  "organization_id": "uuid",
  "name": "My Campaign Workflow"
}
```

---

## Agents

### Agent Hierarchy

```
CEOAgent
├── MarketingDirector
│   ├── ContentSpecialist
│   ├── SEOSpecialist
│   └── SocialSpecialist
├── CreativeDirector
│   ├── Copywriter
│   ├── Designer
│   └── BrandVoice
├── AdvertisingDirector
│   ├── CampaignOptimizer
│   ├── BidManager
│   └── AudienceResearcher
├── ResearchDirector
│   ├── MarketResearcher
│   ├── CompetitorAnalyst
│   └── TrendAnalyzer
├── AnalyticsDirector
│   ├── DataAnalyst
│   ├── AttributionModeler
│   └── ReportGenerator
├── WorkflowDirector
│   ├── WorkflowBuilder
│   ├── AutomationScheduler
│   └── IntegrationManager
└── ComplianceDirector
    ├── ContentReviewer
    ├── PrivacyAuditor
    └── PolicyEnforcer
```

### Execute Agent Task

```http
POST /agents/tasks
Content-Type: application/json

{
  "organization_id": "uuid",
  "agent_type": "ContentSpecialist",
  "task": "Write blog post about AI in marketing",
  "context": {
    "tone": "professional",
    "length": "1500 words",
    "keywords": ["AI", "marketing", "automation"]
  }
}
```

### Get Agent Status

```http
GET /agents/{agent_id}/status
```

---

## Knowledge & Intelligence

### RAG Query

```http
POST /knowledge/rag/query
Content-Type: application/json

{
  "organization_id": "uuid",
  "query": "What are our best performing ad creatives?",
  "max_results": 10,
  "include_sources": true
}
```

### RAG Context

```http
POST /knowledge/rag/context
Content-Type: application/json

{
  "organization_id": "uuid",
  "query": "Brand voice guidelines for social media",
  "max_tokens": 2000
}
```

### Search Knowledge

```http
POST /knowledge/search
Content-Type: application/json

{
  "organization_id": "uuid",
  "query": "Q4 campaign performance",
  "filters": {
    "type": "campaign",
    "date_range": "last_30_days"
  }
}
```

### Predictive Optimization

```http
POST /knowledge/optimize/budget
Content-Type: application/json

{
  "organization_id": "uuid",
  "campaign_ids": ["uuid1", "uuid2"],
  "total_budget": 50000,
  "objective": "maximize_roas"
}
```

### Creative Fatigue Detection

```http
POST /knowledge/optimize/creative-fatigue
Content-Type: application/json

{
  "organization_id": "uuid",
  "campaign_id": "uuid",
  "lookback_days": 30
}
```

### Cross-Campaign Learning

```http
POST /knowledge/cross-campaign/patterns
Content-Type: application/json

{
  "organization_id": "uuid",
  "campaign_ids": ["uuid1", "uuid2", "uuid3"]
}
```

---

## Social Intelligence

### List Campaign Templates

```http
GET /campaigns/templates
GET /campaigns/templates/{template_id}
POST /campaigns/templates/{template_id}/instantiate
Content-Type: application/json

{
  "organization_id": "uuid",
  "name": "New Campaign from Template"
}
```

---

## Workflow Templates

```http
GET /workflows/templates
GET /workflows/templates/{template_id}
POST /workflows/templates/{template_id}/instantiate
Content-Type: application/json

{
  "organization_id": "uuid",
  "name": "My Campaign Workflow"
}
```

---

## Social Intelligence

### List Comments

```http
GET /social/organizations/{organization_id}/comments?platform=meta&sentiment=positive&limit=50
```

### Get Comment

```http
GET /social/organizations/{organization_id}/comments/{comment_id}
```

### Analyze Comment

```http
POST /social/organizations/{organization_id}/comments/{comment_id}/analyze
```

### Moderate Comment

```http
PATCH /social/organizations/{organization_id}/comments/{comment_id}/moderate
Content-Type: application/json

{
  "action": "hide",
  "reason": "Spam content"
}
```

### Generate Auto-Reply

```http
POST /social/organizations/{organization_id}/comments/{comment_id}/reply/generate
```

### Approve Auto-Reply

```http
PATCH /social/organizations/{organization_id}/replies/{reply_id}/approve
```

### Send Auto-Reply

```http
POST /social/organizations/{organization_id}/replies/{reply_id}/send
```

### List Auto-Replies

```http
GET /social/organizations/{organization_id}/replies?status=pending
```

### Get Inbox

```http
POST /social/organizations/{organization_id}/inbox
Content-Type: application/json

{
  "platforms": ["meta"],
  "sentiment_filter": ["negative"],
  "page": 1,
  "page_size": 50
}
```

### Get Inbox Stats

```http
GET /social/organizations/{organization_id}/inbox/stats
```

### Assign Comment

```http
POST /social/organizations/{organization_id}/comments/{comment_id}/assign
Content-Type: application/json

{
  "assignee_id": "uuid"
}
```

### Reply Templates

```http
GET /social/organizations/{organization_id}/reply-templates
POST /social/organizations/{organization_id}/reply-templates
PATCH /social/organizations/{organization_id}/reply-templates/{template_id}
DELETE /social/organizations/{organization_id}/reply-templates/{template_id}
```

### Comment Analytics

```http
GET /social/organizations/{organization_id}/analytics/comments?period_start=2024-01-01&period_end=2024-01-31
```

---

## Shadow Mode

### Create Shadow Session

```http
POST /shadow/organizations/{organization_id}/sessions
Content-Type: application/json

{
  "name": "Campaign Optimizer Shadow",
  "description": "Shadow mode for CampaignOptimizer agent",
  "agent_type": "CampaignOptimizer",
  "agent_model": "gpt-4o",
  "campaigns": ["uuid1", "uuid2"],
  "decision_types": ["budget_adjustment", "bid_optimization"],
  "reviewers": ["uuid1", "uuid2"],
  "require_human_approval": true,
  "auto_approve_threshold": 0.9
}
```

### List Shadow Sessions

```http
GET /shadow/organizations/{organization_id}/sessions?status=enabled
```

### Start Shadow Session

```http
POST /shadow/organizations/{organization_id}/sessions/{session_id}/start
```

### Pause Shadow Session

```http
POST /shadow/organizations/{organization_id}/sessions/{session_id}/pause
```

### End Shadow Session

```http
POST /shadow/organizations/{organization_id}/sessions/{session_id}/end
```

### Get Session Stats

```http
GET /shadow/organizations/{organization_id}/sessions/{session_id}/stats
```

### Record Agent Decision

```http
POST /shadow/organizations/{organization_id}/sessions/{session_id}/decisions/agent
Content-Type: application/json

{
  "decision_type": "budget_adjustment",
  "context": {"current_budget": 5000, "performance": {"roas": 3.2}},
  "entity_id": "campaign-123",
  "entity_type": "campaign",
  "agent_decision": {"action": "increase_budget", "amount": 1000},
  "agent_confidence": 0.85,
  "agent_reasoning": "Strong ROAS trend",
  "agent_model": "gpt-4o"
}
```

### Submit Human Decision

```http
POST /shadow/organizations/{organization_id}/decisions/{decision_id}/human
Content-Type: application/json

{
  "human_decision": {"action": "increase_budget", "amount": 800},
  "human_confidence": 0.9,
  "human_reasoning": "Conservative increase due to seasonality"
}
```

### List Decisions

```http
GET /shadow/organizations/{organization_id}/sessions/{session_id}/decisions
```

### Pending Comparisons

```http
GET /shadow/organizations/{organization_id}/sessions/{session_id}/decisions/pending
```

### Record Outcome

```http
POST /shadow/organizations/{organization_id}/decisions/{decision_id}/outcome
Content-Type: application/json

{
  "outcome": {"roas": 3.5, "spend": 6000, "conversions": 120}
}
```

### Calculate Lift

```http
POST /shadow/organizations/{organization_id}/sessions/{session_id}/lift/calculate
Content-Type: application/json

{
  "metric_name": "roas",
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z",
  "baseline_value": 2.8,
  "agent_value": 3.2,
  "campaigns": ["uuid1", "uuid2"],
  "decision_types": ["bid_optimization"]
}
```

### Get Lift Summary

```http
GET /shadow/organizations/{organization_id}/sessions/{session_id}/lift/summary
```

### Session Events

```http
GET /shadow/organizations/{organization_id}/sessions/{session_id}/events?event_type=decision_compared
```

---

## Observability

### Metrics

```http
POST /observability/organizations/{organization_id}/metrics/definitions
GET /observability/organizations/{organization_id}/metrics/definitions

POST /observability/organizations/{organization_id}/metrics/record
POST /observability/organizations/{organization_id}/metrics/batch

GET /observability/organizations/{organization_id}/metrics/{metric_name}/query?start=...&end=...&aggregation=avg
GET /observability/organizations/{organization_id}/metrics/{metric_name}/series?start=...&end=...
```

### Alerts

```http
POST /observability/organizations/{organization_id}/alerts/rules
GET /observability/organizations/{organization_id}/alerts/rules

POST /observability/organizations/{organization_id}/alerts/evaluate
GET /observability/organizations/{organization_id}/alerts?status=firing

POST /observability/organizations/{organization_id}/alerts/acknowledge
POST /observability/organizations/{organization_id}/alerts/resolve
```

### Cost Tracking

```http
POST /observability/organizations/{organization_id}/costs
GET /observability/organizations/{organization_id}/costs/report?period_start=...&period_end=...

POST /observability/organizations/{organization_id}/budgets
GET /observability/organizations/{organization_id}/budgets
```

### SLA

```http
POST /observability/organizations/{organization_id}/slas
GET /observability/organizations/{organization_id}/slas

POST /observability/organizations/{organization_id}/slas/report
GET /observability/organizations/{organization_id}/slas/{sla_id}/status
```

### Dashboards

```http
POST /observability/organizations/{organization_id}/dashboards
GET /observability/organizations/{organization_id}/dashboards
GET /observability/organizations/{organization_id}/dashboards/default
GET /observability/organizations/{organization_id}/dashboards/{dashboard_id}

POST /observability/organizations/{organization_id}/dashboards/{dashboard_id}/widgets
```

### System Health

```http
GET /observability/organizations/{organization_id}/health
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Format

```json
{
  "type": "https://api.astra-os.com/problems/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request validation failed",
  "instance": "/api/v1/campaigns",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "name",
      "message": "Name is required"
    }
  ]
}
```

---

## Rate Limits

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 60 | 100 |
| Pro | 300 | 500 |
| Enterprise | 1000 | 2000 |

---

## Webhooks

Configure webhooks in Organization Settings to receive real-time events:

- `campaign.created` / `campaign.updated` / `campaign.launched`
- `workflow.created` / `workflow.executed` / `workflow.completed`
- `agent.task_completed` / `agent.task_failed`
- `shadow.decision_made` / `shadow.decision_compared`
- `alert.fired` / `alert.resolved`
- `budget.warning` / `budget.critical`

---

## SDKs

- **Python**: `pip install astra-os-sdk`
- **TypeScript**: `npm install @astra-os/sdk`
- **Go**: `go get github.com/astra-os/sdk-go`

---

## Support

- **Documentation**: https://docs.astra-os.com
- **API Status**: https://status.astra-os.com
- **Support**: support@astra-os.com
- **Community**: https://community.astra-os.com
