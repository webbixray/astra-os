"""Agent management commands for Astra CLI"""

import json
import sys

import click
import requests
from rich.console import Console
from rich.table import Table

from astra_cli.config import load_config


@click.group("agents")
def agents_group():
    """Manage AI agents"""


def _get_headers(config: dict) -> dict:
    """Get API headers with auth"""
    token = config.get("auth", {}).get("token")
    if not token:
        raise click.ClickException("Not authenticated. Run 'astra auth login' first.")
    return {
        "Authorization": f"Bearer {config['auth']['token']}",
        "Content-Type": "application/json",
    }


@agents_group.command("list")
@click.option("--type", "-t", help="Filter by agent type")
@click.option("--status", "-s", help="Filter by status")
@click.option("--limit", "-l", default=50, help="Maximum results")
@click.option("--output", "-o", type=click.Choice(["table", "json", "yaml"]), default="table")
@click.pass_context
def list_agents(ctx: click.Context, type: str, status: str, limit: int, output: str):
    """List all agents"""
    console = Console()
    config = load_config(ctx.obj["config_path"])
    api_url = ctx.obj["api_url"]

    try:
        headers = _get_headers(ctx.obj["config"])
        params = {"limit": limit}
        if type:
            params["type"] = type
        if status:
            params["status"] = status

        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/agents",
            headers=_get_headers(ctx.obj["config"]),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        agents = data.get("agents", [])

        if output == "json":
            import json

            click.echo(json.dumps(agents, indent=2))
            return
        if output == "yaml":
            import yaml

            click.echo(yaml.dump(agents, default_flow_style=False))
            return

        if not agents:
            console.print("[yellow]No agents found[/yellow]")
            return

        table = Table(title=f"Agents ({len(agents)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Organization", style="blue")
        table.add_column("Created", style="dim")

        for agent in agents:
            table.add_row(
                agent.get("id", "")[:8],
                agent.get("name", "N/A"),
                agent.get("type", "N/A"),
                agent.get("status", "unknown"),
                agent.get("organization_id", "N/A")[:8],
                agent.get("created_at", "N/A")[:10],
            )

        console.print(table)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            console.print("[red]Authentication failed. Run 'astra auth login'[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agents_group.command("get")
@click.argument("agent_id")
@click.option("--output", "-o", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def get_agent(ctx: click.Context, agent_id: str, output: str):
    """Get agent details"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj["config"])
        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/agents/{agent_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        agent = response.json()

        if output == "json":
            click.echo(json.dumps(agent, indent=2))
        else:
            import yaml

            click.echo(yaml.dump(agent, default_flow_style=False))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent not found: {agent_id}[/red]")
        elif e.response.status_code == 401:
            console.print("[red]Authentication failed[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agents_group.command("create")
@click.option("--name", "-n", required=True, help="Agent name")
@click.option("--type", "-t", required=True, help="Agent type (CEO, CONTENT_SPECIALIST, etc.)")
@click.option("--description", "-d", help="Agent description")
@click.option("--org", "-o", help="Organization ID")
@click.option(
    "--autonomy", "-a", type=click.Choice(["0", "1", "2"]), default="1", help="Autonomy level"
)
@click.option("--model", "-m", help="Model to use")
@click.option("--input", "-i", help="Input file with agent config (JSON)")
@click.pass_context
def create_agent(
    ctx: click.Context,
    name: str,
    type: str,
    description: str,
    org: str,
    autonomy: str,
    model: str,
    input: str,
):
    """Create a new agent"""
    console = Console()

    config_data = {}
    if input:
        with open(input) as f:
            config_data = json.load(f)

    config_data.update(
        {
            "name": name,
            "type": type,
            "description": description,
            "autonomy_level": int(autonomy),
        }
    )

    if org:
        config_data["organization_id"] = org
    if model:
        config_data["model"] = model

    try:
        headers = _get_headers(ctx.obj["config"])
        response = requests.post(
            f"{ctx.obj['api_url']}/api/v1/agents",
            headers=headers,
            json=config_data,
            timeout=30,
        )
        response.raise_for_status()
        agent = response.json()

        console.print(f"[green]✓[/green] Agent created: {agent['id']}")
        console.print(f"Name: {agent['name']}")
        console.print(f"Type: {agent['type']}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            console.print(f"[red]Validation error: {e.response.json()}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agents_group.command("run")
@click.argument("agent_id")
@click.option("--input", "-i", help="Input data as JSON string")
@click.option("--file", "-f", type=click.File("r"), help="Input file (JSON)")
@click.option("--async", "async_mode", is_flag=True, help="Run asynchronously")
@click.option("--follow", "-f", is_flag=True, help="Follow execution logs")
@click.pass_context
def run_agent(
    ctx: click.Context,
    agent_id: str,
    input: str,
    file: click.File | None,
    async_mode: bool,
    follow: bool,
):
    """Run an agent"""
    console = Console()

    input_data = {}
    if file:
        input_data = json.load(file)
    elif input:
        input_data = json.loads(input)

    try:
        headers = _get_headers(ctx.obj["config"])

        endpoint = f"{ctx.obj['api_url']}/api/v1/agents/{agent_id}/run"
        if async_mode:
            endpoint += "?async=true"

        response = requests.post(
            endpoint,
            headers=headers,
            json=input_data,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        if async_mode:
            task_id = result.get("task_id")
            console.print(f"[green]✓[/green] Started async task: {task_id}")

            if follow:
                console.print("[cyan]Following logs...[/cyan]")
                _follow_task_logs(ctx, task_id)
        elif output == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            console.print("[green]✓[/green] Agent completed")
            console.print(f"Status: {result.get('status')}")
            if result.get("output"):
                console.print(f"Output: {json.dumps(result['output'], indent=2)}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent not found: {agent_id}[/red]")
        elif e.response.status_code == 401:
            console.print("[red]Authentication failed[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agents_group.command("logs")
@click.argument("task_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--lines", "-n", default=100, help="Number of lines")
@click.pass_context
def agent_logs(ctx: click.Context, task_id: str, follow: bool, lines: int):
    """Get agent task logs"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj["config"])
        params = {"lines": lines}
        if follow:
            params["follow"] = "true"

        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/tasks/{task_id}/logs",
            headers=_get_headers(ctx.obj["config"]),
            params=params,
            timeout=30,
            stream=follow,
        )
        response.raise_for_status()

        if follow:
            for line in response.iter_lines():
                if line:
                    console.print(line.decode())
        else:
            logs = response.json()
            for log in logs.get("logs", []):
                console.print(log)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agents_group.command("status")
@click.argument("task_id")
@click.pass_context
def task_status(ctx: click.Context, task_id: str):
    """Get task status"""
    console = Console()

    try:
        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/tasks/{task_id}",
            headers=_get_headers(ctx.obj["config"]),
            timeout=30,
        )
        response.raise_for_status()
        task = response.json()

        table = Table(title=f"Task {task_id}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        for key, value in task.items():
            table.add_row(key, str(value))

        console.print(table)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Task not found: {task_id}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agents_group.command("delete")
@click.argument("agent_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_agent(ctx: click.Context, agent_id: str, force: bool):
    """Delete an agent"""
    console = Console()

    if not force:
        if not click.confirm(f"Delete agent {agent_id}?"):
            console.print("Cancelled")
            return

    try:
        response = requests.delete(
            f"{ctx.obj['api_url']}/api/v1/agents/{agent_id}",
            headers=_get_headers(ctx.obj["config"]),
            timeout=30,
        )
        response.raise_for_status()

        console.print(f"[green]✓[/green] Agent deleted: {agent_id}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Agent not found: {agent_id}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
