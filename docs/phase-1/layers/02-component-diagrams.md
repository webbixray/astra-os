# Phase 1.4: Component & Sequence Diagrams

## System Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────┐
│                        ASTRA OS                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Frontend    │  │    API        │  │   Services    │       │
│  │  (Next.js)    │◀─▶│  (FastAPI)   │◀─▶│  (Python)    │       │
│  └──────────────┘  └──────┬───────┘  └──────┬───────┘       │
│                           │                  │               │
│                           ▼                  ▼               │
│                    ┌──────────────┐  ┌──────────────┐       │
│                    │  PostgreSQL  │  │    Redis     │       │
│                    │  + pgvector  │  │ Cache/Queue  │       │
│                    └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Temporal    │  │  AI Router   │  │  Object Store│       │
│  │  Workflows   │  │  (NVIDIA++)  │  │  (S3/GCS)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
         │               │                │
         ▼               ▼                ▼
  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │ Browser    │  │ 3rd Party  │  │ AI Model   │
  │ (User)     │  │ APIs       │  │ Providers  │
  │            │  │ (Meta,     │  │ (OpenAI,   │
  │            │  │  Google)   │  │  Anthropic)│
  └────────────┘  └────────────┘  └────────────┘
```

## Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ASTRA OS — Containers                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐
│         Next.js App              │
│  ┌────────────────────────────┐  │
│  │  AI Command Center (Widget) │  │
│  │  ┌──────┐ ┌──────┐ ┌────┐  │  │
│  │  │Campgn│ │Content│ │Ads │  │  │
│  │  │Pages │ │Studio │ │Mgr │  │  │
│  │  └──────┘ └──────┘ └────┘  │  │
│  │  ┌──────┐ ┌──────┐ ┌────┐  │  │
│  │  │Analyt│ │Workfl│ │Set │  │  │
│  │  │ ics  │ │  ows  │ │ting│  │  │
│  │  └──────┘ └──────┘ └────┘  │  │
│  │  ┌────────────────────────┐ │  │
│  │  │ Shared Components (UI) │ │  │
│  │  └────────────────────────┘ │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
              │ HTTP/WS
              ▼
┌──────────────────────────────────┐
│      FastAPI Application          │
│  ┌────────────────────────────┐  │
│  │  API Gateway + Auth        │  │
│  │  ┌──────┐ ┌──────┐ ┌────┐  │  │
│  │  │Campgn│ │Content│ │Ads │  │  │
│  │  │Routes│ │Routes│ │Rout│  │  │
│  │  └──────┘ └──────┘ └────┘  │  │
│  │  ┌──────┐ ┌──────┐ ┌────┐  │  │
│  │  │Analyt│ │Workfl│ │Auth│  │  │
│  │  │Routes│ │Routes│ │    │  │  │
│  │  └──────┘ └──────┘ └────┘  │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
              │ Internal
              ▼
┌──────────────────────────────────┐
│     Agent Orchestrator Service   │
│  ┌────────────┐ ┌─────────────┐  │
│  │ Agent      │ │ Agent        │  │
│  │ Runtime    │ │ Registry     │  │
│  ├────────────┤ ├─────────────┤  │
│  │ Memory     │ │ Tool         │  │
│  │ Manager    │ │ Registry     │  │
│  └────────────┘ └─────────────┘  │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│     Workflow Engine Service      │
│  ┌────────────┐ ┌─────────────┐  │
│  │ Temporal   │ │ Workflow     │  │
│  │ Worker     │ │ Compiler     │  │
│  ├────────────┤ ├─────────────┤  │
│  │ Node       │ │ Execution    │  │
│  │ Registry   │ │ Monitor      │  │
│  └────────────┘ └─────────────┘  │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│     AI Router Service            │
│  ┌────────────┐ ┌─────────────┐  │
│  │ Model      │ │ Provider     │  │
│  │ Selector   │ │ Router       │  │
│  ├────────────┤ ├─────────────┤  │
│  │ Cost       │ │ Caching      │  │
│  │ Tracker    │ │ Layer        │  │
│  └────────────┘ └─────────────┘  │
└──────────────────────────────────┘
```

## Key Sequence Diagrams

### 1. User Creates Campaign via AI Command Center

```
User           AI Command Center    Agent Orchestrator   Campaign Service   DB
 │                     │                     │                  │           │
 │  "Create campaign"  │                     │                  │           │
 │────────────────────▶│                     │                  │           │
 │                     │                     │                  │           │
 │                     │  Intent: create     │                  │           │
 │                     │  campaign (context) │                  │           │
 │                     │────────────────────▶│                  │           │
 │                     │                     │                  │           │
 │                     │                     │  Determine gaps   │           │
 │                     │                     │  (no budget,     │           │
 │                     │                     │   no audience)   │           │
 │                     │                     │                  │           │
 │  "What budget and   │  Ask clarifying     │                  │           │
 │   audience?"        │◀────────────────────│                  │           │
 │◀────────────────────│                     │                  │           │
 │                     │                     │                  │           │
 │  "$5000, SaaS       │                     │                  │           │
 │  founders"          │                     │                  │           │
 │────────────────────▶│────────────────────▶│                  │           │
 │                     │                     │                  │           │
 │                     │                     │  CreateCampaign  │           │
 │                     │                     │─────────────────▶│           │
 │                     │                     │                  │  INSERT   │
 │                     │                     │                  │──────────▶│
 │                     │                     │                  │◀──────────│
 │                     │                     │◀─────────────────│           │
 │                     │                     │                  │           │
 │                     │  Campaign created   │                  │           │
 │                     │◀────────────────────│                  │           │
 │  Confirmation +     │                     │                  │           │
 │  next steps        │                     │                  │           │
 │◀────────────────────│                     │                  │           │
```

### 2. Agent Collaboration Flow

```
User          CEO Agent      Marketing Dir    Content Spec    Workflow Engine
 │                │               │                │               │
 │  "Launch       │               │                │               │
 │   campaign"    │               │                │               │
 │───────────────▶│               │                │               │
 │                │               │                │               │
 │                │  Decompose     │                │               │
 │                │  task:         │                │               │
 │                │  - Brief      │                │               │
 │                │  - Create     │                │               │
 │                │  - Schedule   │                │               │
 │                │  - Launch ads │                │               │
 │                │──────────────▶│                │               │
 │                │               │                │               │
 │                │               │  Generate      │               │
 │                │               │  content brief │               │
 │                │               │───────────────▶│               │
 │                │               │                │               │
 │                │               │                │  Draft created │
 │                │               │◀───────────────│               │
 │                │               │                │               │
 │                │               │  Review +       │               │
 │                │               │  approve       │               │
 │                │               │  (or send back) │               │
 │                │               │                │               │
 │                │               │  Schedule post  │               │
 │                │               │────────────────────────────────▶│
 │                │               │                │               │
 │                │  Summary:     │                │               │
 │                │  "Campaign    │                │               │
 │                │   ready"      │                │               │
 │◀───────────────│               │                │               │
 │                │               │                │               │
 │  "Campaign is  │               │                │               │
 │   being set    │               │                │               │
 │   up. Here's   │               │                │               │
 │   the plan..." │               │                │               │
 │◀───────────────│               │                │               │
```

### 3. Workflow Execution Flow

```
User         Workflow Builder    Workflow Compiler    Temporal      Node Runtime
 │                  │                    │                │               │
 │  Build workflow  │                    │                │               │
 │─────────────────▶│                    │                │               │
 │                  │                    │                │               │
 │  Save + Publish  │                    │                │               │
 │─────────────────▶│                    │                │               │
 │                  │  Compile DAG to    │                │               │
 │                  │  Temporal code     │                │               │
 │                  │───────────────────▶│                │               │
 │                  │                    │  Start workflow │               │
 │                  │                    │────────────────▶│               │
 │                  │                    │                │               │
 │                  │                    │                │ Execute Node 1 │
 │                  │                    │                │──────────────▶│
 │                  │                    │                │  (Send email)  │
 │                  │                    │                │◀──────────────│
 │                  │                    │                │               │
 │                  │                    │                │ Execute Node 2 │
 │                  │                    │                │  (API call)   │
 │                  │                    │                │──────────────▶│
 │                  │                    │                │◀──────────────│
 │                  │                    │                │               │
 │                  │                    │                │ Wait for      │
 │                  │                    │                │ approval      │
 │                  │                    │                │──────────────▶│
 │  *notification*  │                    │                │               │
 │◀─────────────────│                    │                │               │
 │                  │                    │                │               │
 │  Approve step    │                    │                │               │
 │─────────────────▶│                    │                │               │
 │                  │                    │                │ Resume        │
 │                  │                    │                │◀──────────────│
 │                  │                    │                │               │
 │                  │                    │  Complete      │               │
 │                  │                    │◀───────────────│               │
 │  Success!        │                    │                │               │
 │◀─────────────────│                    │                │               │
```

### 4. Authentication Flow

```
User         Next.js          Supabase Auth       FastAPI        Database
 │              │                   │                │              │
 │  Login       │                   │                │              │
 │─────────────▶│                   │                │              │
 │              │  POST /auth/login │                │              │
 │              │──────────────────▶│                │              │
 │              │                   │  Validate      │              │
 │              │                   │────────────────▶              │
 │              │                   │◀───────────────│              │
 │              │  JWT {access,     │                │              │
 │              │  refresh}         │                │              │
 │              │◀──────────────────│                │              │
 │              │                   │                │              │
 │              │  Set cookie +     │                │              │
 │              │  redirect to      │                │              │
 │              │  dashboard        │                │              │
 │◀─────────────│                   │                │              │
 │              │                   │                │              │
 │  Load page   │                   │                │              │
 │─────────────▶│   GET /dashboard  │                │              │
 │              │───────────────────────────────────▶│              │
 │              │                   │                │  Verify JWT  │
 │              │                   │                │─────────────▶│
 │              │                   │                │◀─────────────│
 │              │                   │                │              │
 │              │   Dashboard SSR   │                │              │
 │◀─────────────│                   │                │              │
```
