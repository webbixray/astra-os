# Phase 1.6: AI/Agent Architecture

## Agent Orchestrator Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Agent Orchestrator                            │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  Agent        │  │  Agent        │  │  Agent Lifecycle        │   │
│  │  Registry     │  │  Factory      │  │  Manager                │   │
│  ├──────────────┤  ├──────────────┤  ├──────────────────────────┤   │
│  │  Map: type → │  │  Create agent │  │  spawn / pause / resume  │   │
│  │  agent class │  │  with config  │  │  stop / archive          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  Task         │  │  Memory       │  │  Tool Registry          │   │
│  │  Scheduler    │  │  Manager      │  │                          │   │
│  ├──────────────┤  ├──────────────┤  ├──────────────────────────┤   │
│  │  Plan tasks,  │  │  Working     │  │  Register available      │   │
│  │  queue, retry │  │  memory,     │  │  tools per agent type    │   │
│  │  prioritize   │  │  episodic    │  │                          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐                                  │
│  │  Event Bus    │  │  Observability│                                  │
│  │  Adapter      │  │  Collector    │                                  │
│  ├──────────────┤  ├──────────────┤                                  │
│  │  Pub/sub      │  │  Traces,     │                                  │
│  │  domain events│  │  metrics,    │                                  │
│  │               │  │  logs        │                                  │
│  └──────────────┘  └──────────────┘                                  │
└──────────────────────────────────────────────────────────────────────┘
```

## Agent Base Class

```python
class BaseAgent:
    """All agents inherit from this."""
    id: UUID
    agent_type: str
    config: AgentConfig
    memory: MemoryManager
    tools: ToolRegistry

    async def think(self, context: Context) -> Thought:
        """Process input, decide next action."""
        ...

    async def act(self, thought: Thought) -> ActionResult:
        """Execute decided action."""
        ...

    async def reflect(self, result: ActionResult) -> None:
        """Learn from action outcome."""
        ...

    async def collaborate(self, other: 'BaseAgent', task: Task) -> None:
        """Delegate or request from another agent."""
        ...
```

## Agent Lifecycle

```
IDLE
 │
 │ (task assigned)
 ▼
THINKING
 │
 │ (plan formulated)
 ▼
───┬───
   │
   ▼
EXECUTING ◀──── WAITING (for human approval, external data)
   │
   │ (success)
   ▼
REFLECTING
   │
   │ (learned)
   ▼
IDLE
```

## Agent Communication Protocol

Agents communicate via structured messages through the Event Bus:

```json
{
  "type": "agent.message",
  "from": "content_specialist_1",
  "to": "marketing_director_1",
  "correlation_id": "task_abc",
  "message_type": "request_review",
  "payload": {
    "content_id": "content_123",
    "status": "draft_complete",
    "summary": "Generated 3 blog post variants",
    "requires_approval": true
  }
}
```

## Tool Calling Architecture

```
Agent
 │
 │ "I need to create a campaign"
 │
 ▼
Tool Registry
 │
 ├── campaign:create    → Campaign Service (FastAPI)
 ├── content:generate   → AI Router → LLM
 ├── analytics:query    → Analytics Service
 ├── workflow:trigger   → Workflow Engine
 ├── ad:create          → Ad Platform API
 ├── memory:store       → Knowledge Graph
 ├── email:send         → Email Service
 └── slack:notify       → Slack API
```

## Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Memory Manager                              │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Working Memory   │  │ Episodic Memory  │  │ Semantic Memory     │  │
│  │ (Current session) │  │ (Past sessions)  │  │ (Knowledge, facts)  │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────────┤  │
│  │ Conversation     │  │ Previous tasks   │  │ Brand voice         │  │
│  │ Current context  │  │ Campaign history  │  │ Customer segments   │  │
│  │ Active state     │  │ Decisions made   │  │ Best practices      │  │
│  │ Volatile (Redis) │  │ Persisted (PG)   │  │ Persisted (PG+Vec)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      Knowledge Graph                              │ │
│  │  (memory_entries + knowledge_graph_edges + vector search)        │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Model Router Architecture

```
Request
   │
   ▼
┌──────────────┐
│  Classifier   │  ← Determines: task_type, complexity, model_requirements
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Selector     │  ← Maps to {provider, model, params}
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────────┐
│  Rate Limiter │────▶│  Cost Tracker        │
└──────┬───────┘     └─────────────────────┘
       │
       ▼
┌──────────────┐
│  Provider     │
│  Router       │
└──┬───┬───┬───┘
   │   │   │
   ▼   ▼   ▼
 NIM  OpenAI  Anthropic
```

## Observability

Every agent execution produces:
- **Trace**: Full chain of thought with timing
- **Span**: Each tool call, each message, each decision
- **Metric**: Latency, token count, cost, success rate
- **Log**: Structured JSON with agent_id, org_id, correlation_id

## Agent Hierarchy Configuration

```yaml
# agent_hierarchy.yaml
ceo_agent:
  system_prompt: "You are the CEO Agent..."
  model: claude-opus
  temperature: 0.3
  max_iterations: 10
  children:
    - marketing_director
    - creative_director
    - advertising_director
    - research_director
    - analytics_director
    - workflow_director
    - compliance_director
    - memory_manager

marketing_director:
  system_prompt: "..."
  model: claude-sonnet
  temperature: 0.4
  tools: [campaign:*, content:read, analytics:read]
  children:
    - content_specialist
    - seo_specialist
    - social_media_specialist

content_specialist:
  system_prompt: "..."
  model: claude-haiku
  temperature: 0.7
  tools: [content:generate, content:edit, brand:read]
```

## Key Design Decisions

1. **User communicates only with CEO Agent** — internal agent collaboration is invisible
2. **Agents have typed tool access** — content specialist cannot launch ads
3. **Human-in-the-loop for critical actions** — budget spend, content publish, campaign launch
4. **Memory is tiered** — working (volatile), episodic (persistent events), semantic (knowledge)
5. **Observability is mandatory** — every agent action is traced for debugging and compliance
