# ADR-001: Monorepo Structure with Turborepo

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Chief Software Architect, Principal Engineer

## Context

ASTRA OS consists of multiple packages: frontend (Next.js), backend (FastAPI), shared types, AI agents, workflow engine, and various utilities. We need a monorepo strategy that supports code sharing, consistent tooling, and scalable CI.

## Decision

Use **Turborepo** for monorepo management with the following structure:

```
astra/
├── apps/
│   ├── web/                  # Next.js frontend
│   └── api/                  # FastAPI backend
├── packages/
│   ├── shared/               # Shared types, schemas, constants
│   ├── ui/                   # UI component library (shadcn/ui based)
│   ├── config-eslint/        # Shared ESLint config
│   ├── config-typescript/    # Shared TypeScript config
│   └── config-tailwind/      # Shared Tailwind config
├── services/
│   ├── agent-orchestrator/   # AI agent orchestration service
│   ├── workflow-engine/      # Workflow execution service
│   ├── ai-router/            # Multi-model AI router
│   └── knowledge-graph/      # Knowledge graph service
├── docker/
│   ├── dev/                  # Development compose files
│   └── prod/                 # Production compose files
├── docs/                     # Architecture and project docs
├── scripts/                  # Build and deployment scripts
├── turbo.json
├── package.json
└── pnpm-workspace.yaml
```

## Rationale

1. **Shared types**: Single source of truth for Pydantic/Zod schemas between frontend and backend
2. **Parallel builds**: Turborepo caching reduces CI times by 60%+
3. **Consistent tooling**: Single ESLint, TypeScript, Prettier config across all packages
4. **Service isolation**: Backend services in `services/` can be extracted to independent microservices later
5. **pnpm**: Faster than npm/yarn, with strict dependency isolation

## Consequences

- All teams must use pnpm
- Cross-package changes require coordinated PRs
- Initial setup overhead for Turborepo configuration
- Services are logically separated but co-located — extraction to microservices requires minimal refactoring

## Alternatives Considered

- **Nx**: More powerful but heavier; Turborepo's simplicity wins for our team size
- **Single repo (no monorepo)**: Loses shared types and consistent tooling
- **npm workspaces only**: No build caching or parallel execution
