# Phase 1.7: Workflow Engine Architecture

## Overview

The Workflow Engine allows users to create visual automation workflows using a drag-and-drop builder, with AI-powered natural language workflow generation. Execution is handled by Temporal for durability and reliability.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Workflow Engine                                  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Presentation Layer                            │  │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌────────────────┐   │  │
│  │  │ Workflow Builder │  │ Workflow List   │  │ Execution View │   │  │
│  │  │ (React Flow)    │  │ (Data Table)     │  │ (Timeline)     │   │  │
│  │  └─────────────────┘  └────────────────┘  └────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                  │
│                                    ▼                                  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    API Layer (FastAPI)                          │  │
│  │  /workflows • CRUD • compile • deploy • execute • monitor     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                  │
│                                    ▼                                  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Application Layer                            │  │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌────────────────┐   │  │
│  │  │ Workflow         │  │ Workflow        │  │ Node            │   │  │
│  │  │ Definition       │  │ Compiler        │  │ Validator       │   │  │
│  │  │ Service          │  │ (DAG → Code)    │  │                 │   │  │
│  │  └─────────────────┘  └────────────────┘  └────────────────┘   │  │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌────────────────┐   │  │
│  │  │ Workflow         │  │ Template        │  │ AI Workflow    │   │  │
│  │  │ Scheduler        │  │ Manager         │  │ Generator      │   │  │
│  │  └─────────────────┘  └────────────────┘  └────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                  │
│                                    ▼                                  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure Layer                         │  │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌────────────────┐   │  │
│  │  │ Temporal         │  │ Node            │  │ Integration    │   │  │
│  │  │ Worker           │  │ Runtime         │  │ Adapters       │   │  │
│  │  └─────────────────┘  └────────────────┘  └────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## Node Types

### Trigger Nodes (Start)
| Node | Description |
|---|---|
| **Schedule** | Cron-based trigger |
| **Webhook** | Incoming webhook |
| **Event** | Domain event listener |
| **Manual** | User-initiated |
| **Form** | Form submission trigger |

### Action Nodes
| Node | Description |
|---|---|
| **HTTP Request** | API call |
| **AI Generate** | LLM text generation |
| **AI Classify** | LLM classification |
| **AI Extract** | LLM data extraction |
| **Send Email** | Email via provider |
| **Slack Message** | Slack notification |
| **Create Campaign** | ASTRA campaign |
| **Create Content** | ASTRA content |
| **Create Ad** | Ad platform |
| **Update CRM** | External CRM |
| **Database Query** | SQL query |
| **Code** | JavaScript/Python |

### Logic Nodes
| Node | Description |
|---|---|
| **Condition** | If/else branch |
| **Switch** | Multi-branch |
| **Loop** | For each item |
| **Delay** | Wait duration |
| **Wait for Event** | Pause until event |

### Human Nodes
| Node | Description |
|---|---|
| **Approval** | Human approval step |
| **Review** | Human review step |
| **Input** | Human data input |

### Output Nodes
| Node | Description |
|---|---|
| **Return** | Return data |
| **Log** | Log message |
| **Notification** | User notification |

## Workflow Definition Format

```json
{
  "id": "wf_abc123",
  "name": "Campaign Launch Workflow",
  "version": 1,
  "nodes": [
    {
      "id": "node_1",
      "type": "trigger:schedule",
      "position": { "x": 0, "y": 0 },
      "config": {
        "cron": "0 9 * * 1"
      }
    },
    {
      "id": "node_2",
      "type": "action:ai_generate",
      "position": { "x": 300, "y": 0 },
      "config": {
        "prompt": "Generate a weekly social media post about {{campaign.name}}",
        "model": "claude-haiku",
        "output_var": "generated_content"
      }
    },
    {
      "id": "node_3",
      "type": "human:approval",
      "position": { "x": 600, "y": 0 },
      "config": {
        "assignee": "campaign.manager",
        "notify_slack": true
      }
    },
    {
      "id": "node_4",
      "type": "action:create_content",
      "position": { "x": 900, "y": 0 },
      "config": {
        "content": "{{node_2.output.generated_content}}"
      }
    }
  ],
  "edges": [
    { "id": "edge_1", "source": "node_1", "target": "node_2" },
    { "id": "edge_2", "source": "node_2", "target": "node_3" },
    { "id": "edge_3", "source": "node_3", "target": "node_4", "label": "approved" },
    { "id": "edge_4", "source": "node_3", "target": null, "label": "rejected" }
  ]
}
```

## Workflow Compilation

The Workflow Compiler transforms the visual DAG into a Temporal workflow:

```python
# Compiler output (simplified)
@temporal.workflow.defn
class CampaignLaunchWorkflow:
    @temporal.workflow.run
    async def run(self, payload: dict) -> dict:
        # Node 1: Trigger (schedule)
        await workflow.execute_activity(
            schedule_trigger,
            payload["schedule"],
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Node 2: AI Generate
        generated_content = await workflow.execute_activity(
            ai_generate,
            {"prompt": f"Generate weekly post about {payload['campaign_name']}"},
            start_to_close_timeout=timedelta(seconds=60)
        )

        # Node 3: Human Approval
        approved = await workflow.execute_activity(
            request_approval,
            {"content": generated_content, "assignee": payload["manager"]},
            start_to_close_timeout=timedelta(hours=24)
        )

        if not approved:
            return {"status": "rejected", "content": generated_content}

        # Node 4: Create Content
        result = await workflow.execute_activity(
            create_content,
            {"content": generated_content},
            start_to_close_timeout=timedelta(seconds=30)
        )

        return {"status": "published", "content_id": result["id"]}
```

## AI Workflow Generator

The AI Workflow Generator converts natural language to workflow definitions:

```
User: "Every Monday at 9am, generate a social media post about our
current campaign, send it to the campaign manager for approval,
and publish it if approved."

AI: [Generates workflow JSON with schedule trigger → AI generate →
     approval → conditional branch → create content]
```

## Execution Monitoring

```
Workflow Execution
   │
   ├── Temporal Server (history, retries, state)
   │
   ├── Workflow Service (status, progress)
   │
   ├── WebSocket (real-time updates to UI)
   │
   └── Audit Log (all steps recorded)
```

Each execution step produces:
| Event | Description |
|---|---|
| `workflow.started` | Execution began |
| `workflow.node.started` | Node execution started |
| `workflow.node.completed` | Node execution succeeded |
| `workflow.node.failed` | Node execution failed |
| `workflow.node.waiting_approval` | Human approval required |
| `workflow.approval.granted` | Human approved |
| `workflow.approval.denied` | Human rejected |
| `workflow.completed` | Execution finished |
| `workflow.failed` | Execution failed |
