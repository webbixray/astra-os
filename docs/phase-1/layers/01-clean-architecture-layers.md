# Phase 1.2: Clean Architecture Layer Definitions

## Overview

ASTRA OS follows Clean Architecture with four concentric layers. Dependency rule: outer layers depend on inner layers. Nothing in the Domain layer knows about the outside world.

## Layer Definitions

### 1. Domain Layer (Innermost)

**Purpose**: Enterprise business rules and entities. Pure Python — zero external dependencies.

**Contains**:
- Entities (Campaign, User, Content, Workflow, Agent)
- Value Objects (Email, Budget, DateRange, BrandVoice)
- Domain Events (CampaignLaunched, ContentPublished, AgentCompleted)
- Domain Services (BudgetCalculator, ContentApprover)
- Repository Interfaces (not implementations)
- Domain Exceptions

**Rules**:
- No database imports
- No API concerns
- No framework dependencies
- Only standard library + Pydantic (for validation only)
- No side effects (pure functions preferred)
- 100% testable without infrastructure

**Example**:
```python
# domain/entities/campaign.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Campaign:
    id: UUID = field(default_factory=uuid4)
    name: str
    status: CampaignStatus = CampaignStatus.DRAFT
    budget: Budget
    date_range: DateRange
    channels: list[Channel] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def launch(self) -> list[DomainEvent]:
        if self.status != CampaignStatus.DRAFT:
            raise CampaignError("Only draft campaigns can be launched")
        if not self.budget.is_valid():
            raise CampaignError("Budget must be set before launch")
        self.status = CampaignStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        return [CampaignLaunched(campaign_id=self.id)]
```

### 2. Application Layer

**Purpose**: Use cases and application orchestration. Depends only on Domain Layer interfaces.

**Contains**:
- Use Cases / Interactors (CreateCampaignUseCase, LaunchCampaignUseCase)
- DTOs (CampaignDTO, AnalyticsDTO)
- Command/Query objects
- Application Services
- Port interfaces for infrastructure

**Rules**:
- Orchestrates flow between domain and infrastructure
- Does NOT contain business logic — delegates to domain
- Returns DTOs to presentation layer
- Handles transactions, authorization checks
- Depends on abstractions (repository interfaces), not concretions

**Example**:
```python
# application/use_cases/create_campaign.py
class CreateCampaignUseCase:
    def __init__(self, repo: CampaignRepository, event_bus: EventBus):
        self.repo = repo
        self.event_bus = event_bus

    async def execute(self, dto: CreateCampaignDTO, user: User) -> CampaignDTO:
        campaign = Campaign(
            name=dto.name,
            budget=Budget(dto.budget_amount, dto.budget_currency),
            date_range=DateRange(dto.start_date, dto.end_date),
            channels=[Channel(c) for c in dto.channels],
        )
        saved = await self.repo.save(campaign)
        await self.event_bus.publish(CampaignCreated(campaign_id=saved.id))
        return CampaignDTO.from_domain(saved)
```

### 3. Infrastructure Layer

**Purpose**: Implements repository interfaces, database access, external APIs, and framework integration.

**Contains**:
- Database Models (SQLAlchemy ORM)
- Repository Implementations (CampaignRepositoryImpl)
- External API Clients (GoogleAdsClient, MetaAdsClient)
- Cache Implementations (RedisCache)
- Message Queue Adapters
- File Storage Adapters

**Rules**:
- Implements interfaces defined in Domain/Application layers
- Contains all framework-specific code
- Can use ORM, HTTP clients, SDKs
- Must not leak to outer layers
- Repository implementations translate between ORM models and Domain entities

**Example**:
```python
# infrastructure/db/repositories/campaign_repository.py
class CampaignRepositoryImpl(CampaignRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, campaign: Campaign) -> Campaign:
        model = CampaignModel.from_domain(campaign)
        self.session.add(model)
        await self.session.commit()
        return model.to_domain()
```

### 4. Presentation Layer (Backend)

**Purpose**: API routes, request/response handling, serialization.

**Contains**:
- FastAPI route definitions
- Request schemas (Pydantic)
- Response schemas (Pydantic)
- WebSocket handlers
- Middleware (auth, logging, rate limiting)

**Rules**:
- Thin layer — no business logic
- Validates input via Pydantic schemas
- Calls application use cases
- Returns serialized responses

**Example**:
```python
# presentation/routes/campaign_routes.py
@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    request: CreateCampaignRequest,
    use_case: CreateCampaignUseCase = Depends(get_use_case),
    user: User = Depends(get_current_user),
):
    return await use_case.execute(request.to_dto(), user)
```

### 5. Frontend Architecture

The frontend follows a similar layered approach adapted for client-side:

```
┌──────────────────────────────────────────┐
│  Pages / Layouts                         │
│  - App Router pages, root layouts        │
│  - Route groups, error boundaries        │
├──────────────────────────────────────────┤
│  Feature Modules                         │
│  - Components (presentation)             │
│  - Hooks (state + side effects)          │
│  - API layer (server communication)      │
│  - Stores (client state)                 │
│  - Types (local schemas)                 │
├──────────────────────────────────────────┤
│  Shared / UI Library                     │
│  - Design system components             │
│  - Layout primitives                     │
│  - Shared hooks                          │
├──────────────────────────────────────────┤
│  Core / Lib                              │
│  - API client (axios/fetch wrapper)      │
│  - Auth provider + context               │
│  - AI command center (omnipresent)       │
│  - Utilities                             │
└──────────────────────────────────────────┘
```

**Data Flow (Frontend)**:

```
User Interaction
    → React Component (handles events)
    → Custom Hook (state management)
    → API Layer (TanStack Query / fetch)
    → FastAPI Backend
    → Response
    → Hook updates cache (TanStack Query)
    → Component re-renders
```

## Module Dependency Graph

```
dashboard/
├── features/
│   ├── campaigns/       # Can import: shared, lib, ui
│   ├── content/         # Can import: shared, lib, ui
│   ├── analytics/       # Can import: shared, lib, ui
│   ├── workflows/       # Can import: shared, lib, ui (and React Flow)
│   └── settings/        # Can import: shared, lib, ui
├── shared/              # UI primitives, design tokens
├── lib/                 # API client, auth, utils
└── app/                 # Router pages, layouts
```

**Constraint**: Features cannot import from each other. Cross-feature communication happens through the backend API or shared events. If two features share significant logic, extract to a shared package.
