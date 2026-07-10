# ADR-004: Custom Workflow Engine with Temporal for Durability

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Chief Software Architect, Principal Engineer

## Context

ASTRA OS needs a visual workflow builder with conditional logic, branching, loops, human-in-the-loop approvals, and AI-powered natural language workflow generation. Users must be able to create workflows visually and execute them reliably at scale.

## Decision

Build a **custom workflow engine** using **Temporal.io** for execution durability, with a custom visual builder frontend.

### Architecture

```
┌──────────────────────────────────────────┐
│         Visual Workflow Builder          │
│  (React Flow canvas, node palette, UI)   │
├──────────────────────────────────────────┤
│         Workflow Compiler                │
│  (Visual DAG → Temporal workflow code)   │
├──────────────────────────────────────────┤
│         Temporal Worker                  │
│  (Execution, retries, state persistence)  │
├──────────────────────────────────────────┤
│         Node Runtime                     │
│  (200+ node types: AI, API, logic, etc.)  │
└──────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Purpose |
|---|---|---|
| **Workflow Builder UI** | React Flow + custom | Drag-and-drop workflow creation |
| **Workflow Compiler** | Python AST generator | Converts visual graph to Temporal workflow |
| **Temporal Server** | Temporal.io | Durability, retries, state management |
| **Temporal Worker** | Python SDK | Executes workflow steps |
| **Node Registry** | Python plugins | 200+ node type implementations |
| **Execution Monitor** | FastAPI + WebSocket | Real-time workflow execution status |

## Rationale

1. **Temporal provides durability for free** — retries, timeouts, state persistence, history
2. **Custom compiler** allows natural language → workflow generation
3. **Visual builder** differentiates from code-only workflow engines
4. **Node registry pattern** enables extensibility without modifying core engine
5. **Separation of concerns** — builder is frontend, execution is backend

## Consequences

- Temporal adds operational complexity (need Temporal Server cluster)
- Workflow compilation is non-trivial engineering
- Custom node types must be implemented per integration
- State management between builder canvas and Temporal execution history

## Alternatives Considered

- **n8n embedded**: Great builder but cannot match ASTRA OS's required depth; licensing concerns
- **Custom everything**: Temporal is battle-tested at Uber/Netflix; building durability from scratch is unwise
- **Apache Airflow**: Batch-oriented, not suitable for real-time marketing workflows
- **Prefect**: Good DX but less mature than Temporal for durable execution
