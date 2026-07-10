# Phase 1.5: Database Architecture

## Schema Overview

```
astra_db
├── public                    # Shared tables (users, orgs, auth)
├── campaigns                 # Campaign module
├── content                   # Content studio module
├── ads                       # Advertising module
├── analytics                 # Analytics module
├── workflows                 # Workflow engine module
├── agents                    # Agent orchestrator module
├── memory                    # Knowledge graph & memory
└── enterprise                # Enterprise features (audit, billing)
```

## Entity Relationship Summary

### Core Entities

```
Organization 1──* Team 1──* User
Organization 1──* Campaign
Organization 1──* BrandProfile
Organization 1──* Workflow
Organization 1──* Agent

Campaign 1──* Content
Campaign 1──* AdSet
Campaign 1──* CampaignMetric
Campaign 1──* CampaignEvent

User 1──* Notification
User 1──* AuditLog
User 1──* ApiKey
```

## Core Tables

### organizations
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | |
| slug | VARCHAR(100) | Unique, URL-friendly |
| plan_tier | ENUM('free','starter','pro','business','enterprise') | |
| settings | JSONB | Feature flags, preferences |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### users
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR(255) | Unique |
| name | VARCHAR(255) | |
| avatar_url | TEXT | |
| auth_provider_id | VARCHAR(255) | Supabase/Auth0 user ID |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### team_members
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| user_id | UUID | FK → users |
| role | ENUM('owner','admin','member','viewer') | |
| permissions | TEXT[] | Override array |
| joined_at | TIMESTAMPTZ | |

### campaigns
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| name | VARCHAR(255) | |
| description | TEXT | |
| status | ENUM('draft','pending_approval','active','paused','completed','archived') | |
| budget_amount | DECIMAL(12,2) | |
| budget_currency | VARCHAR(3) | ISO 4217 |
| start_date | DATE | |
| end_date | DATE | NULL = ongoing |
| channels | TEXT[] | ['email','social','ads','seo','content'] |
| objective | VARCHAR(100) | 'awareness','consideration','conversion' |
| created_by | UUID | FK → users |
| ai_generated | BOOLEAN | Was AI-generated? |
| metadata | JSONB | Extensible |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### content
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| campaign_id | UUID | FK → campaigns |
| organization_id | UUID | FK → organizations |
| title | VARCHAR(500) | |
| content_type | ENUM('blog','social','email','ad','landing','video_desc') | |
| body | TEXT | HTML/Markdown |
| status | ENUM('draft','review','approved','published','archived') | |
| brand_profile_id | UUID | FK → brand_profiles |
| generated_by_ai | BOOLEAN | |
| ai_prompt | TEXT | Original prompt |
| version | INT | |
| scheduled_at | TIMESTAMPTZ | |
| published_at | TIMESTAMPTZ | |
| created_by | UUID | FK → users |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### content_versions
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| content_id | UUID | FK → content |
| version | INT | |
| title | VARCHAR(500) | |
| body | TEXT | |
| changed_by | UUID | FK → users |
| change_note | TEXT | |
| created_at | TIMESTAMPTZ | |

### ad_sets
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| campaign_id | UUID | FK → campaigns |
| organization_id | UUID | FK → organizations |
| platform | ENUM('google','meta','linkedin','twitter','tiktok') | |
| name | VARCHAR(255) | |
| status | ENUM('draft','active','paused','completed') | |
| daily_budget | DECIMAL(12,2) | |
| total_budget | DECIMAL(12,2) | |
| targeting | JSONB | Audience targeting config |
| creatives | JSONB | Ad creative references |
| platform_campaign_id | VARCHAR(255) | External platform ID |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### workflows
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| name | VARCHAR(255) | |
| description | TEXT | |
| definition | JSONB | Node graph (React Flow format) |
| compiled_code | TEXT | Generated Temporal workflow |
| status | ENUM('draft','published','active','error') | |
| version | INT | |
| created_by | UUID | FK → users |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### workflow_executions
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| workflow_id | UUID | FK → workflows |
| temporal_workflow_id | VARCHAR(255) | Temporal workflow ID |
| status | ENUM('running','completed','failed','cancelled','waiting_approval') | |
| input | JSONB | |
| output | JSONB | |
| error | TEXT | |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

### agents
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| agent_type | VARCHAR(100) | 'ceo','marketing_director','content_specialist', etc. |
| name | VARCHAR(255) | |
| config | JSONB | Model, temperature, system prompt |
| status | ENUM('active','paused','disabled') | |
| parent_agent_id | UUID | Self-referential FK |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### memory_entries
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| memory_type | ENUM('brand','campaign','customer','knowledge','semantic','workflow') | |
| key | VARCHAR(255) | Namespace identifier |
| content | TEXT | |
| embedding | VECTOR(1536) | pgvector |
| metadata | JSONB | |
| source | VARCHAR(100) | 'ai_extracted','manual','system' |
| confidence | DECIMAL(3,2) | |
| created_at | TIMESTAMPTZ | |

### knowledge_graph_edges
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| source_id | UUID | FK → memory_entries |
| target_id | UUID | FK → memory_entries |
| relationship | VARCHAR(100) | 'influences','precedes','contradicts','supports' |
| weight | DECIMAL(5,2) | |
| created_at | TIMESTAMPTZ | |

### analytics_events
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| event_type | VARCHAR(100) | 'page_view','click','conversion','impression' |
| source | VARCHAR(50) | 'google','meta','email','web' |
| campaign_id | UUID | FK → campaigns (nullable) |
| content_id | UUID | FK → content (nullable) |
| properties | JSONB | Custom event properties |
| timestamp | TIMESTAMPTZ | |
| ingested_at | TIMESTAMPTZ | |

### audit_logs
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| organization_id | UUID | FK → organizations |
| user_id | UUID | FK → users |
| action | VARCHAR(100) | 'campaign.create','content.publish','workflow.deploy' |
| resource_type | VARCHAR(50) | 'campaign','content','workflow' |
| resource_id | UUID | |
| details | JSONB | Before/after state |
| ip_address | INET | |
| user_agent | TEXT | |
| created_at | TIMESTAMPTZ | |

## Indexing Strategy

| Table | Index | Type | Rationale |
|---|---|---|---|
| campaigns | (org_id, status) | B-tree | Dashboard queries |
| campaigns | (created_by) | B-tree | User's campaigns |
| content | (campaign_id, status) | B-tree | Campaign content |
| content | (scheduled_at) | B-tree | Scheduling queries |
| workflows | (org_id, status) | B-tree | Workflow listing |
| workflow_executions | (workflow_id) | B-tree | Execution history |
| memory_entries | (org_id, memory_type) | B-tree | Memory queries |
| memory_entries | embedding | IVFFlat (pgvector) | Semantic search |
| analytics_events | (org_id, timestamp) | BRIN | Time-range queries |
| analytics_events | (campaign_id) | B-tree | Campaign analytics |
| audit_logs | (org_id, created_at) | BRIN | Audit queries |

## Migration Strategy

- Alembic for schema migrations
- Each migration is reversible (upgrade + downgrade)
- Naming convention: `YYYY_MM_DD_HHMM_description.py`
- Zero-downtime migrations:
  1. Add new columns as nullable
  2. Backfill data in batches
  3. Add NOT NULL constraint
  4. Remove deprecated columns
- All migrations reviewed in PR
- Staging migration runs before production
