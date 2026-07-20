# ASTRA OS — Phase 5: Developer Experience & Platform Integration

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> Each task = 2-5 min focused work. TDD enforced. Independent reviewer subagent after each task.

**Goal:** World-class developer experience with Backstage integration, CLI tooling, schema registry, and self-service capabilities.

**Architecture:** Clean Architecture + DDD. Target: New `apps/cli/`, `plugins/backstage/`, `tools/schema-registry/`

**Tech Stack:** Python 3.12, TypeScript/React (Backstage), Click/typer (CLI), JSON Schema, OpenAPI

---

## Phase 5A: Astra CLI (`apps/cli/`)

### Task 5.1: Core CLI Structure with Click/Typer

**Objective:** Create installable `astra` CLI with subcommands for all common operations.

**Files:**
- Create: `apps/cli/pyproject.toml`
- Create: `apps/cli/src/astra_cli/__init__.py`
- Create: `apps/cli/src/astra_cli/main.py`
- Create: `apps/cli/src/astra_cli/commands/*.py`

**Commands to implement:**
```bash
astra --version
astra config get/set/list
astra auth login/logout/token
astra agent list/create/run/status/logs
astra workflow list/create/run/status/replay
astra campaign list/create/launch/pause/status
astra dlq list/replay/delete/stats
astra circuit-breaker list/status/reset/force-open
astra slo list/status/burn-rate
astra trace query/follow/download
astra cost report/project/forecast
astra schema validate/generate/docs
astra deploy status/logs/rollback
```

**Step 1: Write failing test**

```python
# apps/cli/tests/test_cli.py
import pytest
from click.testing import CliRunner
from astra_cli.main import cli

def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "astra" in result.output.lower()

def test_config_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "list"])
    assert result.exit_code == 0

def test_agent_list():
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "list"])
    assert result.exit_code == 0
```

**Step 2: Implement core CLI structure**

```python
# apps/cli/src/astra_cli/main.py
import click
from astra_cli.commands import config, agent, workflow, campaign, dlq, circuit_breaker, slo, trace, cost, schema, deploy

@click.group()
@click.version_option(version="0.1.0")
@click.option("--config", "-c", envvar="ASTRA_CONFIG", help="Config file path")
@click.option("--profile", "-p", envvar="ASTRA_PROFILE", help="Profile name")
@click.option("--output", "-o", type=click.Choice(["table", "json", "yaml"]), default="table")
@click.pass_context
def cli(ctx, config, profile, output):
    """Astra OS CLI - AI-Native Marketing & Business Growth Operating System"""
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config
    ctx.obj["profile"] = profile
    ctx.obj["output"] = output

# Register command groups
cli.add_command(config.config_group)
cli.add_command(agent.agent_group)
cli.add_command(workflow.workflow_group)
cli.add_command(campaign.campaign_group)
cli.add_command(dlq.dlq_group)
cli.add_command(circuit_breaker.cb_group)
cli.add_command(slo.slo_group)
cli.add_command(trace.trace_group)
cli.add_command(cost.cost_group)
cli.add_command(schema.schema_group)
cli.add_command(deploy.deploy_group)

if __name__ == "__main__":
    cli()
```

---

### Task 5.2: Auth & Config Commands

**Files:**
- Create: `apps/cli/src/astra_cli/commands/config.py`
- Create: `apps/cli/src/astra_cli/commands/auth.py`

```python
# config.py
import click
import yaml
from astra_cli.config import load_config, save_config, get_config_value, set_config_value

@click.group(name="config")
def config_group():
    """Manage Astra configuration"""
    pass

@config_group.command("list")
@click.option("--profile", "-p", help="Profile to list")
def config_list(profile):
    """List all configuration values"""
    config = load_config(profile)
    click.echo(yaml.dump(config, default_flow_style=False))

@config_group.command("get")
@click.argument("key")
def config_get(key):
    """Get a configuration value"""
    value = get_config_value(key)
    click.echo(value)

@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value"""
    set_config_value(key, value)
    click.echo(f"Set {key} = {value}")
```

---

### Task 5.3: Agent Management Commands

**Files:**
- Create: `apps/cli/src/astra_cli/commands/agent.py`

```python
# agent.py
import click
import json
from astra_cli.api import AgentAPI

@click.group(name="agent")
def agent_group():
    """Manage AI agents"""
    pass

@agent_group.command("list")
@click.option("--type", "-t", help="Filter by agent type")
@click.option("--status", "-s", help="Filter by status")
def agent_list(type, status):
    """List all agents"""
    api = AgentAPI()
    agents = api.list_agents(type=type, status=status)
    click.echo(json.dumps(agents, indent=2))

@agent_group.command("run")
@click.argument("agent_type")
@click.option("--input", "-i", help="Input data as JSON")
@click.option("--file", "-f", type=click.File("r"), help="Input file")
@click.option("--async", "async_mode", is_flag=True, help="Run asynchronously")
def agent_run(agent_type, input, file, async_mode):
    """Run an agent"""
    api = AgentAPI()
    input_data = json.load(file) if file else json.loads(input or "{}")

    if async_mode:
        task_id = api.run_agent_async(agent_type, input_data)
        click.echo(f"Started async task: {task_id}")
    else:
        result = api.run_agent(agent_type, input_data)
        click.echo(json.dumps(result, indent=2))

@agent_group.command("status")
@click.argument("task_id")
def agent_status(task_id):
    """Get agent task status"""
    api = AgentAPI()
    status = api.get_task_status(task_id)
    click.echo(json.dumps(status, indent=2))

@agent_group.command("logs")
@click.argument("task_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
def agent_logs(task_id, follow):
    """Get agent task logs"""
    api = AgentAPI()
    logs = api.get_task_logs(task_id, follow=follow)
    for log in logs:
        click.echo(log)
```

---

## Phase 5B: Backstage Plugin (`plugins/backstage/`)

### Task 5.4: Backstage Plugin Structure

**Files:**
- Create: `plugins/backstage/plugin/package.json`
- Create: `plugins/backstage/plugin/src/index.ts`
- Create: `plugins/backstage/plugin/src/components/*.tsx`

```json
// package.json
{
  "name": "@astra-os/backstage-plugin",
  "version": "0.1.0",
  "description": "Astra OS Backstage Plugin",
  "main": "src/index.ts",
  "scripts": {
    "build": "tsc",
    "lint": "eslint src --ext .ts,.tsx",
    "test": "jest"
  },
  "dependencies": {
    "@backstage/core-plugin-api": "^1.0.0",
    "@backstage/core-components": "^1.0.0",
    "@backstage/core-app-api": "^1.0.0",
    "@material-ui/core": "^4.12.0",
    "react": "^17.0.0",
    "react-router-dom": "^6.0.0"
  }
}
```

---

### Task 5.5: Entity Definitions (catalog-info.yaml)

**Objective:** Define Astra OS entities for Backstage catalog.

```yaml
# template entity definitions
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: astra-agent-orchestrator
  description: "Agent Orchestrator service for Astra OS"
  annotations:
    github.com/project-slug: webbixray/astra-os
    backstage.io/techdocs-ref: dir:.
  tags:
    - python
    - fastapi
    - ai-agents
    - orchestration
spec:
  type: service
  lifecycle: production
  owner: team-astra
  system: astra-os
  providesApis:
    - astra-agent-api

---
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: astra-api
  description: "Astra OS API Gateway"
  annotations:
    github.com/project-slug: webbixray/astra-os
  tags:
    - python
    - fastapi
    - api-gateway
spec:
  type: service
  lifecycle: production
  owner: team-astra
  system: astra-os
  providesApis:
    - astra-public-api

---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: astra-agent-api
  description: "Agent Orchestrator API"
spec:
  type: openapi
  lifecycle: production
  owner: team-astra
  system: astra-os
  definition:
    $text: https://api.astra-os.io/openapi.json
```

---

### Task 5.6: Backstage UI Components

**Files:**
- Create: `plugins/backstage/plugin/src/components/AgentDashboard.tsx`
- Create: `plugins/backstage/plugin/src/components/CircuitBreakerPanel.tsx`
- Create: `plugins/backstage/plugin/src/components/DLQPanel.tsx`
- Create: `plugins/backstage/plugin/src/components/CostTracker.tsx`
- Create: `plugins/backstage/plugin/src/components/TraceExplorer.tsx`

```tsx
// AgentDashboard.tsx
import React from 'react';
import {
  Page,
  Header,
  Content,
  Card,
  Grid,
  Table,
  Progress,
} from '@backstage/core-components';
import { useApi, configApiRef } from '@backstage/core-plugin-api';

interface Agent {
  id: string;
  type: string;
  status: 'running' | 'completed' | 'failed';
  runs: number;
  successRate: number;
  avgDuration: number;
  tokensUsed: number;
  cost: number;
}

export const AgentDashboard = () => {
  const configApi = useApi(configApiRef);
  const [agents, setAgents] = React.useState<Agent[]>([]);

  React.useEffect(() => {
    // Fetch from Astra API
    fetch(`${configApi.getBaseUrl()}/api/v1/agents`)
      .then(r => r.json())
      .then(setAgents);
  }, []);

  return (
    <Page themeId="home">
      <Header title="Astra Agents" subtitle="Agent Orchestrator Dashboard" />
      <Content>
        <Grid container spacing={3}>
          {agents.map(agent => (
            <Grid item xs={12} sm={6} md={4} key={agent.id}>
              <Card>
                <Card.Content>
                  <Typography variant="h6">{agent.type}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {agent.status} • {agent.runs} runs
                  </Typography>
                  <Progress variant="determinate" value={agent.successRate * 100} />
                  <Table>
                    <TableBody>
                      <TableRow>
                        <TableCell>Avg Duration</TableCell>
                        <TableCell>{agent.avgDuration}s</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Tokens Used</TableCell>
                        <TableCell>{agent.tokensUsed.toLocaleString()}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Cost</TableCell>
                        <TableCell>${agent.cost.toFixed(4)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </Card.Content>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Content>
    </Page>
  );
};

export default AgentDashboard;
```

---

## Phase 5C: Schema Registry (`tools/schema-registry/`)

### Task 5.7: JSON Schema Registry

**Files:**
- Create: `tools/schema-registry/src/registry.py`
- Create: `tools/schema-registry/src/generator.py`
- Create: `tools/schema-registry/src/validator.py`

```python
# registry.py
"""JSON Schema Registry for Astra OS"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from jsonschema import Draft202012Validator

@dataclass
class SchemaEntry:
    name: str
    version: str
    schema: Dict[str, Any]
    description: str
    examples: list

class SchemaRegistry:
    """Central registry for all Astra OS JSON schemas"""

    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self._schemas: Dict[str, SchemaEntry] = {}
        self._validators: Dict[str, Draft202012Validator] = {}
        self._load_all()

    def _load_all(self):
        for schema_file in self.schema_dir.rglob("*.json"):
            with open(schema_file) as f:
                data = json.load(f)

            # Extract metadata from schema
            name = data.get("$id", schema_file.stem)
            version = data.get("version", "1.0.0")
            description = data.get("description", "")
            examples = data.get("examples", [])

            entry = SchemaEntry(
                name=name,
                version=version,
                schema=data,
                description=description,
                examples=examples,
            )

            self._schemas[name] = entry
            self._validators[name] = Draft202012Validator(data)

    def get(self, name: str) -> Optional[SchemaEntry]:
        return self._schemas.get(name)

    def validate(self, name: str, data: Dict[str, Any]) -> tuple[bool, list]:
        """Validate data against schema. Returns (is_valid, errors)"""
        validator = self._validators.get(name)
        if not validator:
            return False, [f"Schema '{name}' not found"]

        errors = list(validator.iter_errors(data))
        return len(errors) == 0, [e.message for e in errors]

    def generate_example(self, name: str) -> Optional[Dict[str, Any]]:
        """Generate example data from schema"""
        entry = self._schemas.get(name)
        if entry and entry.examples:
            return entry.examples[0]
        return None

    def list_schemas(self) -> list[str]:
        return list(self._schemas.keys())

    def get_openapi_components(self) -> Dict[str, Any]:
        """Export all schemas as OpenAPI components"""
        return {
            name: entry.schema
            for name, entry in self._schemas.items()
        }
```

---

### Task 5.8: Schema Generator from Pydantic Models

**Files:**
- Create: `tools/schema-registry/src/generator.py`

```python
# generator.py
"""Generate JSON Schemas from Pydantic models"""

import json
from pydantic import BaseModel
from typing import Type, get_type_hints
from pydantic.json_schema import GenerateJsonSchema

def generate_schema_from_model(model: Type[BaseModel]) -> dict:
    """Generate JSON Schema from a Pydantic model"""
    generator = GenerateJsonSchema(
        by_alias=True,
        ref_template="#/components/schemas/{model}"
    )

    schema = generator.generate(model.model_json_schema())
    return schema

def generate_all_schemas(models_module) -> dict:
    """Generate schemas for all Pydantic models in a module"""
    import inspect

    schemas = {}
    for name, obj in inspect.getmembers(models_module):
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
            schema = generate_schema_from_model(obj)
            schemas[obj.__name__] = schema
    return schemas

def save_schemas(schemas: dict, output_dir: Path):
    """Save schemas to JSON files"""
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, schema in schemas.items():
        file_path = output_dir / f"{name}.json"
        with open(file_path, "w") as f:
            json.dump(schema, f, indent=2)

        print(f"Generated: {file_path}")
```

---

## Phase 5D: Self-Service APIs

### Task 5.9: API for Agent/Workflow Self-Service

**Files:**
- Create: `apps/api/app/presentation/routes/self_service.py`

```python
# self_service.py
"""Self-service API endpoints for developers"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

router = APIRouter(prefix="/api/v1/self-service", tags=["self-service"])

class AgentRunRequest(BaseModel):
    agent_type: str
    input_data: dict
    async_mode: bool = False
    priority: int = 0

class AgentRunResponse(BaseModel):
    task_id: UUID
    status: str
    result: Optional[dict] = None

class WorkflowCreateRequest(BaseModel):
    name: str
    description: str
    definition: dict  # DAG definition
    template_id: Optional[str] = None

@router.post("/agents/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    """Run an agent (self-service)"""
    # Validate agent type exists
    # Check rate limits
    # Queue task
    pass

@router.get("/agents/{task_id}/status")
async def get_agent_status(task_id: UUID):
    """Get agent task status"""
    pass

@router.get("/agents/{task_id}/logs")
async def get_agent_logs(task_id: UUID, follow: bool = False):
    """Get agent task logs"""
    pass

@router.post("/workflows", response_model=dict)
async def create_workflow(request: WorkflowCreateRequest):
    """Create a workflow from definition or template"""
    pass

@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: UUID):
    pass

@router.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: UUID, input_data: dict):
    pass

@router.get("/schemas/{schema_name}")
async def get_schema(schema_name: str):
    """Get JSON schema by name"""
    pass
```

---

## Phase 5E: Documentation & SDK

### Task 5.10: Python SDK (`sdk/python/`)

**Files:**
- Create: `sdk/python/astra_sdk/__init__.py`
- Create: `sdk/python/astra_sdk/client.py`
- Create: `sdk/python/astra_sdk/models.py`

```python
# client.py
"""Astra OS Python SDK"""

import httpx
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel

class AstraClient:
    """Astra OS API Client"""

    def __init__(
        self,
        base_url: str = "https://api.astra-os.io",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # Agent methods
    async def run_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        async_mode: bool = False,
    ) -> Dict[str, Any]:
        response = await self.client.post(
            "/api/v1/self-service/agents/run",
            json={
                "agent_type": agent_type,
                "input_data": input_data,
                "async_mode": async_mode,
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_agent_status(self, task_id: str) -> Dict[str, Any]:
        response = await self.client.get(f"/api/v1/self-service/agents/{task_id}/status")
        response.raise_for_status()
        return response.json()

    # Workflow methods
    async def create_workflow(self, name: str, definition: Dict, template_id: str = None) -> Dict:
        response = await self.client.post(
            "/api/v1/self-service/workflows",
            json={"name": name, "definition": definition, "template_id": template_id}
        )
        response.raise_for_status()
        return response.json()

    # Schema methods
    async def get_schema(self, schema_name: str) -> Dict:
        response = await self.client.get(f"/api/v1/self-service/schemas/{schema_name}")
        response.raise_for_status()
        return response.json()

    # Cost methods
    async def get_cost_report(
        self,
        start_date: str,
        end_date: str,
        group_by: str = "agent_type",
    ) -> Dict:
        response = await self.client.get(
            "/api/v1/self-service/cost/report",
            params={"start": start_date, "end": end_date, "group_by": group_by}
        )
        response.raise_for_status()
        return response.json()
```

---

## Verification Checklist

- [ ] Task 5.1: Core CLI structure with all command groups
- [ ] Task 5.2: Auth & Config commands
- [ ] Task 5.3: Agent management commands
- [ ] Task 5.4: Backstage plugin structure
- [ ] Task 5.5: Entity definitions
- [ ] Task 5.6: Backstage UI components (AgentDashboard, CircuitBreakerPanel, DLQPanel, CostTracker, TraceExplorer)
- [ ] Task 5.7: JSON Schema Registry
- [ ] Task 5.8: Schema Generator from Pydantic
- [ ] Task 5.9: Self-Service API endpoints
- [ ] Task 5.10: Python SDK
- [ ] All tests pass
- [ ] CLI installable via `pip install astra-cli`
- [ ] Backstage plugin installable via `@astra-os/backstage-plugin`
- [ ] Schema registry generates valid OpenAPI components

---

## Execution Order

1. **Task 5.1** → Core CLI structure
2. **Task 5.2** → Auth & Config commands
3. **Task 5.3** → Agent management commands
4. **Task 5.4** → Backstage plugin structure
5. **Task 5.5** → Entity definitions
6. **Task 5.6** → Backstage UI components
7. **Task 5.7** → JSON Schema Registry
8. **Task 5.8** → Schema Generator
9. **Task 5.9** → Self-Service API
10. **Task 5.10** → Python SDK

---

**Next Action:** Begin **Task 5.1** — Create `apps/cli/` with core CLI structure.
