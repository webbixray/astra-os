# ADR-006: Multi-Model AI Router with NVIDIA NIM Primary

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, AI Research Scientist, Infrastructure Architect

## Context

ASTRA OS must support multiple AI models across different providers for cost optimization, reliability, and capability matching. Simple tasks should use cheap/fast models; complex reasoning should use advanced models. The system must gracefully handle provider outages.

## Decision

Build a **Multi-Model AI Router** with NVIDIA NIM as the primary inference backend, with OpenAI, Anthropic, and Gemini as fallbacks.

### Router Architecture

```
User Request
    │
    ▼
┌─────────────────────┐
│   Intent Classifier  │  ← Classifies task type & complexity
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Model Selector     │  ← Maps task → optimal model
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Provider Router    │  ← Primary → fallback chain
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐ ┌────────┐
│ NVIDIA │ │ OpenAI │  ...
│  NIM   │ │        │
└────────┘ └────────┘
```

### Model Mapping

| Task Type | Primary Model | Fallback | Cost Tier |
|---|---|---|---|
| Simple generation (tweets, subject lines) | NVIDIA NIM Llama-3-70B | Gemini Flash | Cheap |
| Complex generation (blog posts, landing pages) | NVIDIA NIM Llama-3-70B | Claude Haiku | Medium |
| Code / structured output | Claude Sonnet | GPT-4o | Medium |
| Complex reasoning / planning | Claude Opus | GPT-4o | Expensive |
| Analysis / classification | GPT-4o Mini | Gemini Flash | Cheap |
| Memory summarization | Gemini Flash | Llama-3-70B | Cheap |
| Knowledge graph extraction | Claude Sonnet | GPT-4o | Medium |
| Workflow generation | Claude Opus | GPT-4o | Expensive |

### Routing Strategy

1. **Primary**: NVIDIA NIM (self-hosted on-prem or cloud GPU)
2. **Fallback 1**: OpenAI (GPT-4o / GPT-4o Mini)
3. **Fallback 2**: Anthropic (Claude Opus / Sonnet / Haiku)
4. **Fallback 3**: Google Gemini (Ultra / Pro / Flash)

### Cost Optimization

- Low-complexity tasks automatically routed to cheapest adequate model
- Token usage tracked per agent, per workflow, per org
- Monthly cost budgets with soft/hard caps
- Caching layer for identical requests (TTL-based)

## Rationale

1. **NVIDIA NIM provides predictable latency and cost** when self-hosted
2. **Multi-provider fallback ensures availability** — no single point of failure
3. **Task-based routing optimizes cost** — simple tasks use cheap models
4. **Model mapping is configurable** — can be adjusted as new models release
5. **Avoids vendor lock-in** — switching dominant model is a config change

## Consequences

- NVIDIA NIM requires GPU infrastructure (on-prem or cloud)
- Model capabilities change frequently — routing config needs regular updates
- Need benchmarking pipeline to validate model selection
- Token counting and cost attribution adds engineering overhead

## Alternatives Considered

- **Single provider (OpenAI-only)**: Simple but expensive and single point of failure
- **LiteLLM**: Good library but doesn't provide the routing intelligence we need
- **AWS Bedrock**: Vendor lock-in and limited model selection
- **Ollama**: Great for local dev but not production-scale
