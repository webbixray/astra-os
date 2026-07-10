# ADR-005: PostgreSQL with pgvector as Primary Database

**Status**: Accepted
**Date**: 2026-07-09
**Deciders**: CTO, Database Architect, Infrastructure Architect

## Context

ASTRA OS needs to store relational data (campaigns, users, organizations), vector embeddings (memory, knowledge graph), time-series data (analytics), and JSON documents (workflow definitions, agent state). Using multiple databases increases operational complexity.

## Decision

Use **PostgreSQL** as the primary database with **pgvector** extension for embeddings, and **Redis** for caching/queues/pub-sub.

### Database Strategy

| Data Type | Storage | Rationale |
|---|---|---|
| **Relational** (users, orgs, campaigns, content) | PostgreSQL | ACID compliance, relational integrity |
| **Vector embeddings** (memory, semantic search) | PostgreSQL + pgvector | Avoid operational overhead of separate vector DB |
| **Time-series** (analytics, metrics) | PostgreSQL + TimescaleDB (if needed) | Evaluate at scale; materialized views first |
| **JSON/Schemaless** (workflow definitions, agent state) | PostgreSQL JSONB | Native JSON support with indexing |
| **Session cache** | Redis | TTL-based, fast |
| **Task queue** | Redis (Celery/Bull) | Well-understood pattern |
| **Rate limiting** | Redis | Atomic counters |
| **Pub/sub** | Redis | Real-time updates |

### Partitioning Strategy

- **Organizations**: Separate schema per enterprise tenant (enterprise tier)
- **Time-based**: Analytics tables partitioned by month
- **Size-based**: Large JSONB fields (workflow definitions) in separate tables

### Migration Strategy

- Alembic for schema migrations
- Every migration must be reversible
- Zero-downtime migrations required for production
- Migration plan reviewed as part of PR process

## Rationale

1. **Single database reduces operational complexity** — one backup strategy, one connection pool, one monitoring setup
2. **pgvector is production-ready** and avoids network round-trips to a separate vector database
3. **JSONB provides flexibility** for schemaless data without losing relational capabilities
4. **PostgreSQL ecosystem** is mature with excellent tooling (Alembic, SQLAlchemy, pgAdmin)
5. **Cost-effective** compared to multi-DB setups (Pinecone + PostgreSQL + Redis)

## Consequences

- pgvector performance degrades at very high dimensions (>2000) — monitor and consider dedicated vector DB at scale
- JSONB indexing requires careful planning for query performance
- TimescaleDB extension for time-series if analytics volume exceeds PostgreSQL's capabilities
- Need connection pooling (PgBouncer) for production

## Alternatives Considered

- **Neo4j** (Knowledge graph): Could replace pgvector for certain queries but adds operational cost; consider in Phase 3 if graph complexity requires it
- **Pinecone/Milvus**: Best-in-class vector search but adds network call per query and doubles operational cost
- **MongoDB**: Schemaless but loses relational integrity; not suitable for transactional data
- **ClickHouse**: Excellent for analytics but columnar store is poor for transactional workloads
