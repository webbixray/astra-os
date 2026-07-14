# Tempo TraceQL Queries for ASTRA OS

This document contains common TraceQL queries for debugging and analyzing Astra OS distributed traces.

## Basic Queries

### Find all agent runs
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" }
```

### Find slow agent runs (>10s)
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" && duration > 10s }
```

### Find failed agent runs
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" && attributes["agent.success"] = false }
```

### Find specific agent type runs
```traceql
{ span.kind = "internal" && name = "agent.CEO.run" }
{ span.kind = "internal" && name = "agent.CONTENT_SPECIALIST.run" }
```

## Tool Call Queries

### Find all tool calls
```traceql
{ span.kind = "client" && name =~ "agent\..*\.call_tool" }
```

### Find slow tool calls (>5s)
```traceql
{ span.kind = "client" && name =~ "agent\..*\.call_tool" && duration > 5s }
```

### Find failed tool calls
```traceql
{ span.kind = "client" && name =~ "agent\..*\.call_tool" && attributes["tool.success"] = false }
```

### Find specific tool calls
```traceql
{ span.kind = "client" && name =~ "agent\..*\.call_tool" && attributes["tool.name"] = "web_search" }
```

### Find tool calls by agent type
```traceql
{ span.kind = "client" && name =~ "agent\..*\.call_tool" && attributes["agent.type"] = "CEO" }
```

## Delegation Queries

### Find all delegations
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.delegate" }
```

### Find failed delegations
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.delegate" && attributes["subagent.success"] = false }
```

### Find delegations by target type
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.delegate" && attributes["subagent.type"] = "CONTENT_SPECIALIST" }
```

### Find delegation chains (parent -> child -> grandchild)
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.delegate" }
|> count by (trace_id)
|> filter (count > 2)
```

## Governance & Compliance Queries

### Find governance blocks
```traceql
{ events.name = "governance.blocked" }
```

### Find governance blocks by tool
```traceql
{ events.name = "governance.blocked" && events.attributes["tool.name"] = "web_search" }
```

### Find governance blocks by autonomy level
```traceql
{ events.name = "governance.blocked" && events.attributes["agent.autonomy_level"] = 1 }
```

### Find approval required events
```traceql
{ events.name = "governance.approval_required" }
```

## Circuit Breaker Queries

### Find circuit breaker state changes
```traceql
{ attributes["circuit_breaker.state"] != "" }
```

### Find open circuits
```traceql
{ attributes["circuit_breaker.state"] = "open" }
```

### Find circuit breaker rejections
```traceql
{ events.name = "circuit_breaker.rejected" }
```

## Error & Exception Queries

### Find all spans with exceptions
```traceql
{ span.status = "error" }
```

### Find specific exception types
```traceql
{ span.status = "error" && span.events.name = "exception" && span.events.attributes["exception.type"] = "RuntimeError" }
```

### Find HTTP 5xx errors
```traceql
{ span.kind = "client" && attributes["http.status_code"] >= 500 }
```

## Tenant & Organization Queries

### Find traces for specific tenant
```traceql
{ resource.attributes["tenant.id"] = "tenant-123" }
```

### Find traces for specific organization
```traceql
{ resource.attributes["organization.id"] = "org-456" }
```

### Find traces by user
```traceql
{ resource.attributes["user.id"] = "user-789" }
```

## Cost & Token Queries

### Find high-cost traces (> $0.01)
```traceql
{ attributes["agent.cost_usd"] > 0.01 }
```

### Find high-token traces (> 1000 tokens)
```traceql
{ attributes["agent.tokens_used"] > 1000 }
```

### Find traces by provider
```traceql
{ attributes["ai.provider"] = "openai" }
{ attributes["ai.provider"] = "anthropic" }
{ attributes["ai.provider"] = "nvidia_nim" }
```

## Latency Analysis

### Find P95 latency traces
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" && duration > 30s }
```

### Compare latency by agent type
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" }
|> select(agent_type = attributes["agent.type"], duration)
|> avg(duration) by (agent_type)
```

### Find tail latency traces (top 5%)
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" }
|> quantile(0.95, duration)
```

## Correlation & Root Cause

### Find traces with both governance block and error
```traceql
{ events.name = "governance.blocked" }
|> union { span.status = "error" }
```

### Find traces where delegation failed after tool call
```traceql
{ span.kind = "client" && name =~ "agent\..*\.call_tool" && attributes["tool.success"] = false }
|> union { span.kind = "internal" && name =~ "agent\..*\.delegate" && attributes["subagent.success"] = false }
```

### Find traces by correlation ID
```traceql
{ trace_id = "abc123def456" }
```

## Advanced Patterns

### Find retry patterns
```traceql
{ events.name = "tool.call.exception" }
|> union { events.name = "tool.call.failed" }
```

### Find cascading failures
```traceql
{ span.kind = "internal" && name =~ "agent\..*\.run" && attributes["agent.success"] = false }
|> select(trace_id)
|> join({ span.kind = "internal" && name =~ "agent\..*\.delegate" && attributes["subagent.success"] = false }, trace_id)
```

### Find resource exhaustion traces
```traceql
{ span.status = "error" && attributes["error"] =~ ".*(memory|timeout|quota).*" }
```

## Performance Baselines

### Agent run duration by type (expected ranges)
| Agent Type | Expected P50 | Expected P95 | Alert Threshold |
|------------|-------------|--------------|-----------------|
| CEO | < 5s | < 15s | > 30s |
| MARKETING_DIRECTOR | < 3s | < 10s | > 20s |
| CONTENT_SPECIALIST | < 2s | < 8s | > 15s |
| SEO_SPECIALIST | < 3s | < 10s | > 20s |
| DESIGNER | < 5s | < 15s | > 30s |

### Tool call duration baselines
| Tool | Expected P50 | Expected P95 |
|------|-------------|--------------|
| web_search | < 1s | < 3s |
| python | < 2s | < 5s |
| database_query | < 500ms | < 1s |
| api_call | < 1s | < 3s |

## Useful Grafana Tempo Dashboards

### 1. Agent Performance Overview
- Service map showing agent → tool → provider calls
- RED metrics per agent type
- Error rate by agent type

### 2. Governance & Compliance
- Governance blocks over time
- Blocks by tool / autonomy level
- Approval rate trends

### 3. Circuit Breaker Health
- Circuit states timeline
- Fallback activation rate
- Recovery time after OPEN

### 4. Cost Attribution
- Cost by agent type / tenant / provider
- Token usage trends
- Budget burn rate

## Running Queries in Grafana

1. Open Grafana → Explore
2. Select Tempo datasource
3. Paste TraceQL query
4. Adjust time range
5. Run query

## Automation

These queries can be used in:
- Automated anomaly detection
- SLO burn rate calculations
- Incident response runbooks
- Chaos engineering verification

---

*Document version: 1.0*
*Last updated: 2025-07-14*