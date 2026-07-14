"""Workflow management commands for Astra CLI"""

import json
import sys

import click
import requests
from rich.console import Console
from rich.table import Table


@click.group("workflows")
def workflows_group():
    """Manage workflows"""


def _get_headers(config: dict) -> dict:
    """Get API headers with auth"""
    token = config.get("auth", {}).get("token")
    if not token:
        raise click.ClickException("Not authenticated. Run 'astra auth login' first.")
    return {
        "Authorization": f"Bearer {config['auth']['token']}",
        "Content-Type": "application/json",
    }


@click.command("list")
@click.option("--status", "-s", help="Filter by status")
@click.option("--org", "-O", help="Organization ID")
@click.option("--limit", "-l", default=50, help="Maximum results")
@click.option("--output", "-O", type=click.Choice(["table", "json", "yaml"]), default="table")
@click.pass_context
def list_workflows(ctx: click.Context, status: str, org: str, limit: int, output: str):
    """List all workflows"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj.get("config", {}))
        api_url = ctx.obj.get("api_url", "https://api.astra-os.io")
        params = {"limit": limit}
        if status:
            params["status"] = status
        if org:
            params["organization_id"] = org

        response = requests.get(
            f"{api_url}/api/v1/workflows",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        workflows = data.get("workflows", [])

        if output == "json":
            click.echo(json.dumps(workflows, indent=2))
            return
        if output == "yaml":
            import yaml
            click.echo(yaml.dump(workflows, default_flow_style=False))
            return

        if not workflows:
            console.print("[yellow]No workflows found[/yellow]")
            return

        table = Table(title=f"Workflows ({len(workflows)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Version", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Organization", style="blue")
        table.add_column("Updated", style="dim")

        for wf in workflows:
            table.add_row(
                wf.get("id", "")[:8],
                wf.get("name", "N/A"),
                wf.get("version", "N/A"),
                wf.get("status", "unknown"),
                wf.get("organization_id", "N/A")[:8],
                wf.get("updated_at", "N/A")[:10],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command("get")
@click.argument("workflow_id")
@click.option("--output", "-o", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def get_workflow(ctx: click.Context, workflow_id: str, output: str):
    """Get workflow details"""
    console = Console()

    try:
        api_url = ctx.obj.get("api_url", "https://api.astra-os.io")

        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/workflows/{workflow_id}",
            headers=_get_headers(ctx.obj.get("config", {})),
            timeout=30,
        )
        response.raise_for_status()
        workflow = response.json()

        if output == "json":
            click.echo(json.dumps(workflow, indent=2))
        else:
            import yaml
            click.echo(yaml.dump(workflow, default_flow_style=False))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Workflow not found: {workflow_id}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command("create")
@click.option("--name", "-n", required=True, help="Workflow name")
@click.option("--description", "-d", help="Workflow description")
@click.option("--definition", "-D", help="Workflow definition file (JSON/YAML)")
@click.option("--org", "-o", help="Organization ID")
@click.pass_context
def create_workflow(ctx: click.Context, name: str, description: str, definition: str, org: str):
    """Create a new workflow"""
    console = Console()

    definition_data = {}
    if definition:
        import yaml
        with open(definition) as f:
            if definition.endswith((".yaml", ".yml")):
                definition_data = yaml.safe_load(f)
            else:
                definition_data = json.load(f)

    data = {
        "name": name,
        "description": description,
        "definition": definition_data,
    }
    if org:
        data["organization_id"] = org

    try:
        headers = _get_headers(ctx.obj.get("config", {}))
        api_url = ctx.obj.get("api_url", "https://api.astra-os.io")

        response = requests.post(
            f"{api_url}/api/v1/workflows",
            headers=_get_headers(ctx.obj.get("config", {})),
            json={"name": name, "description": description, "definition": definition_data, "organization_id": org},
            timeout=30,
        )
        response.raise_for_status()
        workflow = response.json()

        console.print(f"[green]✓[/green] Workflow created: {workflow['id']}")
        console.print(f"Name: {workflow['name']}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            console.print(f"[red]Validation error: {e.response.json()}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command("run")
@click.argument("workflow_id")
@click.option("--input", "-i", help="Input data as JSON string")
@click.option("--file", "-F", type=click.File("r"), help="Input file (JSON)")
@click.option("--async", "async_mode", is_flag=True, help="Run asynchronously")
@click.option("--follow", "-w", is_flag=True, help="Follow execution")
@click.pass_context
def run_workflow(ctx: click.Context, workflow_id: str, input: str, file, async_mode: bool, follow: bool):
    """Run a workflow"""
    console = Console()

    input_data = {}
    if file:
        import yaml
        if file.name.endswith((".yaml", ".yml")):
            input_data = yaml.safe_load(file)
        else:
            input_data = json.load(file)
    elif input:
        input_data = json.loads(input)

    try:
        headers = _get_headers(ctx.obj.get("config", {}))
        api_url = ctx.obj.get("api_url", "https://api.astra-os.io")
        endpoint = f"{api_url}/api/v1/workflows/{workflow_id}/run"
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
                console.print("[cyan]Following execution...[/cyan]")
                _follow_task_logs(ctx, task_id)
        else:
            console.print("[green]✓[/green] Workflow completed")
            console.print(f"Status: {result.get('status')}")
            if result.get("output"):
                console.print(f"Output: {json.dumps(result['output'], indent=2)}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command("executions")
@click.argument("workflow_id")
@click.option("--status", "-s", help="Filter by status")
@click.option("--limit", "-l", default=20, help="Maximum results")
@click.pass_context
def workflow_executions(ctx: click.Context, workflow_id: str, status: str, limit: int):
    """List workflow executions"""
    console = Console()

    try:
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/workflows/{workflow_id}/executions",
            headers=_get_headers(ctx.obj.get("config", {})),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        executions = data.get("executions", [])

        if not executions:
            console.print("[yellow]No executions found[/yellow]")
            return

        table = Table(title=f"Executions ({len(executions)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="dim")
        table.add_column("Completed", style="dim")
        table.add_column("Duration", style="magenta")

        for exec in executions:
            table.add_row(
                exec.get("id", "")[:8],
                exec.get("status", "unknown"),
                exec.get("started_at", "N/A")[:19],
                exec.get("completed_at", "N/A")[:19],
                f"{exec.get('duration_ms', 0)/1000:.1f}s",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command("delete")
@click.argument("workflow_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_workflow(ctx: click.Context, workflow_id: str, force: bool):
    """Delete a workflow"""
    console = Console()

    if not force:
        if not click.confirm(f"Delete workflow {workflow_id}?"):
            console.print("Cancelled")
            return

    try:
        response = requests.delete(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/workflows/{workflow_id}",
            headers=_get_headers(ctx.obj.get("config", {})),
            timeout=30,
        )
        response.raise_for_status()

        console.print(f"[green]✓[/green] Workflow deleted: {workflow_id}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Workflow not found: {workflow_id}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Group all workflow commands
workflows_cli = click.Group("workflows", help="Manage workflows")
workflows_cli.add_command(list_workflows, name="list")
workflows_cli.add_command(get_workflow, name="get")
workflows_cli.add_command(create_workflow, name="create")
workflows_cli.add_command(run_workflow, name="run")
workflows_cli.add_command(workflow_executions, name="executions")
workflows_cli.add_command(delete_workflow, name="delete")


def _follow_task_logs(ctx: click.Context, task_id: str):
    """Follow task logs (placeholder)"""
