# ADR-009: Event-Driven Architecture with Redis Pub/Sub

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Chief Software Architect, SRE

## Context

ASTRA OS has multiple services that need to react to events: campaign launched → analytics calculates baseline → agents receive context → workflows trigger → notifications sent. Synchronous coupling between these creates latency and fragility.

## Decision

Adopt **Event-Driven Architecture** using **Redis Pub/Sub** for real-time events and **PostgreSQL LISTEN/NOTIFY** for domain events, with a migration path to **RabbitMQ** or **Kafka** when volume requires.

### Event Architecture

```
┌──────────┐     Domain Events     ┌──────────┐
│  Campaign │──── pg_notify ──────▶│   Agent   │
│  Service  │                      │Orchestrator│
└──────────┘                      └──────────┘
      │                                  │
      │ Redis Pub/Sub                    │
      ▼                                  ▼
┌──────────┐                      ┌──────────┐
│Analytics │                      │ Workflow │
│ Service  │                      │  Engine  │
└──────────┘                      └──────────┘
```

### Event Categories

| Category | Examples | Delivery | Persistence |
|---|---|---|---|
| **Domain Events** | campaign.launched, content.published, ad.completed | pg_notify | PostgreSQL (audit table) |
| **Real-time Events** | agent.progress, workflow.step, user.action | Redis Pub/Sub | Not persisted |
| **System Events** | error.threshold, usage.limit, deployment | pg_notify + log | PostgreSQL + Logger |
| **Analytics Events** | page.view, conversion, click | Redis Stream (batch) | PostgreSQL (batch insert) |

### Event Schema

```json
{
  "id": "evt_abc123",
  "type": "campaign.launched",
  "version": 1,
  "timestamp": "2026-07-09T12:00:00Z",
  "org_id": "org_xyz",
  "actor": "user_abc",
  "data": {
    "campaign_id": "camp_123",
    "channels": ["email", "social", "ads"],
    "budget": 5000
  },
  "trace_id": "trace_abc123",
  "correlation_id": "corr_xyz"
}
```

### Event Flow Example

```
1. User launches campaign via AI Command Center
2. Campaign Service creates event: campaign.launched
3. pg_notify delivers event to subscribed services
4. Analytics Service: starts baseline calculation
5. Agent Orchestrator: provides context to agents
6. Workflow Engine: triggers post-launch workflows
7. Notification Service: sends campaign launch notification
8. All services acknowledge with event_id
```

## Rationale

1. **Loose coupling** between services enables independent deployment and scaling
2. **Traceability** via correlation_id enables full request tracing across services
3. **pg_notify** is zero-infrastructure for domain events within PostgreSQL
4. **Redis Pub/Sub** is familiar to the team and sufficient for v1 volume
5. **Standardized event schema** enables consistent observability

## Consequences

- Redis Pub/Sub is at-most-once delivery — no message persistence if consumer is down
- pg_notify has a 8KB payload limit — large events need reference via ID
- Event schema versioning required for backward compatibility
- Need dead letter queue for failed event processing
- Migration to Kafka/RabbitMQ will be needed at scale

## Alternatives Considered

- **Kafka**: Event persistence, replay, partitioning but operational complexity for v1
- **RabbitMQ**: Good balance of features and complexity; consider for Phase 3
- **Celery**: Task-queue oriented, not designed for event broadcasting
- **gRPC streaming**: Requires persistent connections; poor for broadcast events
