# Agent Orchestrator Runtime

The Agent Orchestrator is the core runtime for managing and executing AI agents in ASTRA OS. It provides a hierarchical agent system with memory management, tool execution, and inter-agent communication.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
├─────────────────────────────────────────────────────────────┤
│  Agent Registry  │  Tool Registry  │  Memory Manager         │
├─────────────────────────────────────────────────────────────┤
│  Hierarchy       │  Communication  │  Events                 │
├─────────────────────────────────────────────────────────────┤
│  Tools           │  Sandbox        │  Memory (PG + Redis)    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Agent Runtime (`runtime/agent.py`)
- **Base Agent Class**: Abstract base for all agents
- **Agent Registry**: Registration and instantiation of agent types
- **Agent Context**: Execution context with tenant isolation
- **Agent State Management**: Lifecycle tracking

### Tool System (`runtime/tools.py`)
- **Tool Registry**: Dynamic tool registration and discovery
- **Execution Sandbox**: Secure code/command execution
- **Built-in Tools**: Web search, Python execution, file operations

### Memory System (`runtime/memory.py`)
- **Working Memory**: Redis-backed, short-term (1hr TTL)
- **Episodic Memory**: PostgreSQL-backed, execution traces
- **Semantic Memory**: PostgreSQL + pgvector for knowledge
- **Memory Consolidation**: Promote important memories

### Event System (`runtime/events.py`)
- **Event Bus**: Pub/sub for agent and system events
- **Filtered Subscriptions**: Event filtering by type/source/tags
- **Event History**: In-memory event replay

### Hierarchy (`runtime/hierarchy.py`)
- **Agent Hierarchy**: 3-level hierarchy (CEO → Directors → Specialists)
- **Communication Protocol**: Message passing between agents
- **Handoff Manager**: Task delegation with capabilities matching
- **Agent Coordinator**: Parallel/sequential/consensus execution

### Tool System (`runtime/tools.py`)
- **Tool Registry**: Dynamic registration and discovery
- **Execution Sandbox**: Secure Python/command execution
- **Type Validation**: Parameter validation against schemas
- **Rate Limiting**: Per-tool rate limiting

## Agent Hierarchy

```
CEO Agent
├── Marketing Director
│   ├── Content Specialist
│   ├── SEO Specialist
│   └── Social Specialist
├── Creative Director
│   ├── Copywriter
│   ├── Designer
│   └── Brand Voice
├── Advertising Director
│   ├── Campaign Optimizer
│   ├── Bid Manager
│   └── Audience Researcher
├── Research Director
│   ├── Market Researcher
│   ├── Competitor Analyst
│   └── Trend Analyzer
├── Analytics Director
│   ├── Data Analyst
│   ├── Attribution Modeler
│   └── Report Generator
├── Workflow Director
│   ├── Workflow Builder
│   ├── Automation Scheduler
│   └── Integration Manager
└── Compliance Director
    ├── Content Reviewer
    ├── Privacy Auditor
    └── Policy Enforcer
```

## Quick Start

```bash
# Install dependencies
pip install -e "services/agent-orchestrator[dev]"

# Run the orchestrator
python -m services.agent_orchestrator

# Or run the main entry point
python services/agent-orchestrator/main.py
```

## Configuration

Environment variables (`.env`):

```bash
# Database
DATABASE_URL=postgresql://astra:astra_dev@localhost:5432/astra

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8001

# Agent Runtime
AGENT_POOL_SIZE=10
DEFAULT_AGENT_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
```

## Usage

### Creating an Agent

```python
from services.agent_orchestrator.runtime import (
    Agent,
    AgentConfig,
    AgentType,
    get_agent_registry,
)

registry = get_agent_registry()
agent = registry.create_agent(
    AgentType.CONTENT_SPECIALIST,
    tenant_id=uuid4(),
)
```

### Running an Agent

```python
from services.agent_orchestrator.runtime import AgentContext

context = AgentContext(
    agent_id=agent.config.agent_id,
    tenant_id=tenant_id,
)

result = await agent.run(context, "Write a blog post about AI in marketing")
```

### Using Tools

```python
from services.agent_orchestrator.runtime import tool_registry

# Register a custom tool
class MyTool(Tool):
    definition = ToolDefinition(
        name="my_tool",
        description="Does something useful",
        parameters=[...],
    )
    async def execute(self, **params):
        return {"result": "done"}

tool_registry.register(MyTool(MyTool.definition))
```

### Using Memory

```python
from services.agent_orchestrator.runtime import memory_manager

# Store a memory
await memory_manager.store(
    agent_id=agent_id,
    tenant_id=tenant_id,
    memory_type="episodic",
    key="campaign_launch_2024",
    value={"campaign": "Q1 Launch", "result": "success"},
    importance=0.8,
    tags=["campaign", "success"],
)

# Retrieve memories
memories = await memory_manager.retrieve(
    agent_id=agent_id,
    tenant_id=tenant_id,
    memory_type="episodic",
    limit=10,
)
```

### Event Bus

```python
from services.agent_orchestrator.runtime import publish_event, subscribe

# Publish
await publish_event(
    event_type="campaign.launched",
    source="campaign_service",
    payload={"campaign_id": "123", "budget": 10000},
    tags=["campaign", "launch"],
)

# Subscribe
unsubscribe = subscribe("campaign.launched", handle_campaign_launch)
```

## Agent Types

### CEO Agent
- Strategic planning and delegation
- Cross-functional coordination
- High-level decision making

### Directors (7)
- Marketing, Creative, Advertising, Research, Analytics, Workflow, Compliance

### Specialists (21)
- Content, SEO, Social, Copywriter, Designer, Brand Voice
- Campaign Optimizer, Bid Manager, Audience Researcher
- Market Researcher, Competitor Analyst, Trend Analyzer
- Data Analyst, Attribution Modeler, Report Generator
- Workflow Builder, Automation Scheduler, Integration Manager
- Content Reviewer, Privacy Auditor, Policy Enforcer

## Autonomy Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| 0 (Advisory) | Suggests actions, requires approval | New agents, sensitive operations |
| 1 (Semi-Auto) | Executes with notifications | Routine operations |
| 2 (Full Auto) | Executes independently | Trusted, bounded operations |

## Security

- **Tenant Isolation**: All operations scoped to tenant
- **Sandbox Execution**: Code runs in restricted environment
- **Rate Limiting**: Per-tool rate limits
- **Approval Gates**: Human-in-the-loop for sensitive actions
- **Audit Logging**: All actions logged to PostgreSQL

## Testing

```bash
# Run tests
pytest services/agent-orchestrator/tests

# Type checking
mypy services/agent-orchestrator

# Linting
ruff check services/agent-orchestrator
ruff format services/agent-orchestrator
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents` | GET | List agents |
| `/api/v1/agents` | POST | Create agent |
| `/api/v1/agents/{id}` | GET | Get agent |
| `/api/v1/agents/{id}/run` | POST | Execute agent |
| `/api/v1/agents/{id}/tools` | GET | List agent tools |
| `/api/v1/memory` | GET | Query memory |
| `/api/v1/events` | GET | Event stream |

## Monitoring

- **Metrics**: Prometheus `/metrics` endpoint
- **Health**: `/health` and `/ready` endpoints
- **Traces**: OpenTelemetry integration
- **Logs**: Structured JSON logging

## License

Proprietary - ASTRA OS