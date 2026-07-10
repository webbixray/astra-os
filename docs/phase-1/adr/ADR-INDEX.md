# Architecture Decision Records

| # | Title | Decision | Date |
|---|---|---|---|
| 001 | Monorepo Structure | Turborepo + pnpm | 2026-07-09 |
| 002 | Clean Architecture | Feature-first modules, 4-layer separation | 2026-07-09 |
| 003 | Agent Orchestrator | Custom hierarchical agent system (not LangGraph/CrewAI) | 2026-07-09 |
| 004 | Workflow Engine | Custom visual builder + Temporal for durability | 2026-07-09 |
| 005 | Database | PostgreSQL + pgvector (primary), Redis (cache/queue/pubsub) | 2026-07-09 |
| 006 | AI Model Router | Multi-model router: NVIDIA NIM primary → OpenAI → Anthropic → Gemini | 2026-07-09 |
| 007 | Frontend Framework | Next.js 15 + App Router + RSC streaming + shadcn/ui | 2026-07-09 |
| 008 | Authentication | Supabase Auth v1 → Auth0 (enterprise); JWT + OAuth/OIDC | 2026-07-09 |
| 009 | Event-Driven | Redis Pub/Sub + PostgreSQL LISTEN/NOTIFY → Kafka (future) | 2026-07-09 |
