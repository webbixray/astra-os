# ADR-003: Custom Agent Orchestrator (Not LangGraph/CrewAI)

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Chief Software Architect, AI Research Scientist

## Context

ASTRA OS requires hierarchical agents (CEO → Directors → Specialists) with persistent memory, tool calling, inter-agent communication, and enterprise governance. Several open-source frameworks exist (LangGraph, CrewAI, AutoGen, Semantic Kernel).

## Decision

Build a **custom Agent Orchestrator** on top of a lightweight agent framework layer.

### Architecture

```
┌─────────────────────────────────────┐
│         Agent Orchestrator          │
│  (Coordination, lifecycle, routing)  │
├─────────────────────────────────────┤
│         Agent Runtime                │
│  (Execution sandbox, tool registry)  │
├─────────────────────────────────────┤
│         Model Router                 │
│  (NVIDIA NIM primary → fallbacks)    │
├─────────────────────────────────────┤
│         Memory / Context             │
│  (Working memory, episodic, semantic) │
└─────────────────────────────────────┘
```

### Agent Hierarchy

```
CEO Agent
├── Marketing Director
│   ├── Content Specialist
│   ├── SEO Specialist
│   └── Social Media Specialist
├── Creative Director
│   ├── Copywriter Agent
│   ├── Designer Agent
│   └── Brand Voice Agent
├── Advertising Director
│   ├── Campaign Optimizer
│   ├── Bid Manager
│   └── Audience Researcher
├── Research Director
│   ├── Market Researcher
│   ├── Competitor Analyst
│   └── Trend Analyzer
├── Analytics Director
│   ├── Data Analyst
│   ├── Attribution Modeler
│   └── Report Generator
├── Workflow Director
│   ├── Workflow Builder
│   ├── Automation Scheduler
│   └── Integration Manager
├── Compliance Director
│   ├── Content Reviewer
│   ├── Privacy Auditor
│   └── Policy Enforcer
└── Memory Manager
    ├── Knowledge Graph Operator
    ├── Brand Memory Curator
    └── Performance Historian
```

## Rationale

1. **Hierarchical architecture not supported by LangGraph/CrewAI** — they assume flat agent teams
2. **Enterprise governance** — need RBAC at agent level, audit trails, approval workflows
3. **Persistence** — agents must remember across sessions and campaigns
4. **Observability** — need full execution tracing for debugging and compliance
5. **Vendor independence** — not locked into any framework's evolution

## Consequences

- Higher initial build cost (~20 person-weeks vs ~5 for existing frameworks)
- Ongoing maintenance of agent runtime
- Need for rigorous testing of agent collaboration patterns
- Documentation and on-call knowledge required

## Alternatives Considered

- **LangGraph**: Best for DAG-based agent workflows but lacks hierarchical support and enterprise features
- **CrewAI**: Simple API but immature for production; no RBAC, no audit
- **AutoGen**: Microsoft-backed but experimental; breaking changes frequent
- **Semantic Kernel**: .NET-centric; not ideal for Python stack
