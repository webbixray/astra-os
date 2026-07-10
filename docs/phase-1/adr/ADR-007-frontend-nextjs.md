# ADR-007: Next.js 15 with App Router and Server Components

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Chief Software Architect, Frontend Team

## Context

ASTRA OS requires a modern, performant frontend with real-time updates, optimistic UI, streaming AI responses, and excellent developer experience. The frontend must support complex state management across 10+ feature domains.

## Decision

Use **Next.js 15** with the **App Router**, **React Server Components**, **shadcn/ui**, **TanStack Query**, and **Zustand**.

### Technology Stack

| Category | Choice | Rationale |
|---|---|---|
| **Framework** | Next.js 15 (App Router) | SSR, RSC, streaming, file-based routing |
| **UI Library** | shadcn/ui + Radix | Accessible, customizable, dark mode |
| **Styling** | Tailwind CSS v4 | Utility-first, fast iteration |
| **State (Server)** | TanStack Query v5 | Caching, optimistic updates, WebSocket sync |
| **State (Client)** | Zustand | Lightweight, no boilerplate, middleware support |
| **Forms** | React Hook Form + Zod | Performant, schema-based validation |
| **Animation** | Framer Motion | Declarative, gesture support, layout animations |
| **Charts** | Recharts / Tremor | Composable, React-native charting |
| **Flow Builder** | React Flow | Mature node-based UI library |
| **Rich Text** | TipTap / Plate | ProseMirror-based, extensible |
| **Testing** | Vitest + Playwright | Fast unit tests + browser E2E |

### Rendering Strategy

| Page Type | Rendering | Rationale |
|---|---|---|
| Public pages (landing, pricing) | SSG | Static, CDN-cached |
| Dashboard pages | SSR + Streaming | Dynamic per user, fast initial load |
| Analytics pages | SSR + ISR | Pre-render with background revalidation |
| AI responses | Streaming (RSC) | Real-time token-by-token display |
| Workflow builder | CSR | Complex interactive state |

### Component Architecture

```
app/
├── (marketing)/        # Landing, pricing, docs (SSG)
├── (dashboard)/        # Authenticated layout
│   ├── campaigns/      # Campaign pages
│   ├── content/        # Content studio
│   ├── ads/            # Advertising studio
│   ├── analytics/      # Analytics dashboards
│   ├── workflows/      # Workflow builder
│   ├── settings/       # Organization settings
│   └── ai/             # AI Command Center (omnipresent)
└── api/                # API routes (proxy to FastAPI)
```

## Rationale

1. **RSC streaming** enables real-time AI response display without WebSocket complexity for initial v1
2. **shadcn/ui** provides accessible, customizable components with dark mode by default
3. **TanStack Query** handles server state caching, background refetching, and optimistic updates
4. **Zustand** is simpler than Redux for client state that TanStack Query doesn't cover
5. **React Hook Form + Zod** gives type-safe forms with minimal re-renders

## Consequences

- RSC streaming requires careful API design
- Zustand stores need clear boundaries to avoid spaghetti
- React Flow integration with RSC requires client boundaries
- Bundle size monitoring required for shadcn/ui tree-shaking

## Alternatives Considered

- **Remix**: Great for forms but weaker streaming support
- **Nuxt**: Vue-based; team preference is React/TS
- **Vite + React Router**: Loses SSR, SEO, and RSC benefits
- **Redux Toolkit**: Too much boilerplate for our state needs
