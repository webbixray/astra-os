# ADR-002: Clean Architecture with Feature-First Modules

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Chief Software Architect, Principal Engineer

## Context

The system spans 10+ domain areas (campaigns, content, ads, analytics, agents, workflows, etc.). Each has complex business logic, database access, API endpoints, and UI components. We need an architecture that keeps domains decoupled, testable, and independently evolvable.

## Decision

Adopt **Clean Architecture** with **Feature-First Module Organization**.

### Layer Definitions (Backend — FastAPI)

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│  (API routes, WebSocket handlers)   │
├─────────────────────────────────────┤
│         Application Layer           │
│  (Use cases, DTOs, commands/queries) │
├─────────────────────────────────────┤
│         Domain Layer                │
│  (Entities, Value Objects, Events)   │
├─────────────────────────────────────┤
│         Infrastructure Layer        │
│  (DB repositories, external APIs)   │
└─────────────────────────────────────┘
```

### Layer Definitions (Frontend — Next.js)

```
┌─────────────────────────────────────┐
│         Pages / Layouts             │
│  (App Router, layouts, pages)       │
├─────────────────────────────────────┤
│         Features                    │
│  (Feature modules, each with:       │
│   components, hooks, api, stores)   │
├─────────────────────────────────────┤
│         Shared / UI                 │
│  (Design system, shared components)  │
├─────────────────────────────────────┤
│         Lib / Utils                 │
│  (API client, auth, utilities)      │
└─────────────────────────────────────┘
```

### Feature Module Structure (Backend)

```
campaigns/
├── domain/
│   ├── entities/
│   │   ├── campaign.py
│   │   └── campaign_status.py
│   ├── value_objects/
│   │   ├── budget.py
│   │   └── date_range.py
│   └── events/
│       └── campaign_launched.py
├── application/
│   ├── use_cases/
│   │   ├── create_campaign.py
│   │   ├── launch_campaign.py
│   │   └── get_campaign_analytics.py
│   └── dto/
│       └── campaign_dto.py
├── infrastructure/
│   ├── db/
│   │   ├── models/
│   │   │   └── campaign_model.py
│   │   └── repositories/
│   │       └── campaign_repository.py
│   └── api/
│       └── campaign_client.py
├── presentation/
│   ├── routes.py
│   └── schemas.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── __init__.py
```

### Feature Module Structure (Frontend)

```
campaigns/
├── components/
│   ├── CampaignList.tsx
│   ├── CampaignCard.tsx
│   └── CampaignForm.tsx
├── hooks/
│   ├── useCampaigns.ts
│   └── useCampaignMutations.ts
├── api/
│   └── campaignApi.ts
├── stores/
│   └── campaignStore.ts
├── types/
│   └── campaign.ts
└── tests/
    └── CampaignList.test.tsx
```

## Rationale

1. **Domain isolation**: Each feature module is independently testable and deployable
2. **Dependency inversion**: Domain layer has zero external dependencies
3. **Testability**: Use cases can be tested without infrastructure
4. **Parallel development**: Multiple teams can work on different features simultaneously
5. **Evolution**: Modules can be extracted to microservices when needed

## Consequences

- More boilerplate compared to flat structure
- Strict enforcement required in code review
- Dependency injection setup needed for repository pattern
- Team training required on Clean Architecture principles

## Alternatives Considered

- **Flat structure**: Fast initial velocity but unsustainable at scale
- **MVC**: Tight coupling between layers; difficult to test business logic in isolation
- **Microservices from day one**: Premature; adds operational complexity before product-market fit
