"""Schema management commands for Astra CLI"""

import json
import sys

import click
import requests
import yaml
from rich.console import Console
from rich.table import Table


@click.group("schemas")
def schemas_group():
    """Manage and validate JSON schemas"""


def _get_config_and_url(ctx: click.Context) -> tuple[dict, str]:
    """Get config and API URL from context"""
    config = ctx.obj.get("config", {})
    if not config:
        # Load from config_path
        config_path = ctx.obj.get("config_path")
        if config_path:
            from astra_cli.config import load_config

            config = load_config(config_path)
        else:
            from astra_cli.config import load_config

            config = load_config()
    api_url = ctx.obj.get("api_url", "https://api.astra-os.io")
    return config, api_url


def _get_headers(config: dict) -> dict:
    """Get API headers with auth"""
    token = config.get("auth", {}).get("token")
    if not token:
        raise click.ClickException("Not authenticated. Run 'astra auth login' first.")
    return {
        "Authorization": f"Bearer {config['auth']['token']}",
        "Content-Type": "application/json",
    }


@schemas_group.command("list")
@click.option("--output", "-o", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def list_schemas(ctx: click.Context, output: str):
    """List all available schemas"""
    console = Console()

    try:
        config, api_url = _get_config_and_url(ctx)
        headers = _get_headers(config)
        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/schemas",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        schemas = data.get("schemas", [])

        if output == "json":
            click.echo(json.dumps(schemas, indent=2))
            return

        if not schemas:
            console.print("[yellow]No schemas found[/yellow]")
            return

        table = Table(title=f"Available Schemas ({len(schemas)})")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description", style="white")
        table.add_column("Examples", style="dim")

        for schema in schemas:
            table.add_row(
                schema.get("name", "N/A"),
                schema.get("version", "N/A"),
                schema.get("description", "")[:60],
                str(len(schema.get("examples", []))),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schemas_group.command("get")
@click.argument("schema_name")
@click.option("--output", "-o", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def get_schema(ctx: click.Context, schema_name: str, output: str):
    """Get schema by name"""
    console = Console()

    try:
        config, api_url = _get_config_and_url(ctx)
        headers = _get_headers(config)
        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/schemas/{schema_name}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        schema = response.json()

        if output == "json":
            click.echo(json.dumps(schema, indent=2))
        else:
            click.echo(yaml.dump(schema, default_flow_style=False))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Schema not found: {schema_name}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schemas_group.command("validate")
@click.argument("schema_name")
@click.option("--file", "-f", type=click.File("r"), help="Data file to validate (JSON/YAML)")
@click.option("--data", "-d", help="Inline JSON data to validate")
@click.pass_context
def validate_schema(ctx: click.Context, schema_name: str, file, data: str):
    """Validate data against a schema"""
    console = Console()

    # Load data to validate
    if file:
        import yaml

        content = file.read()
        if file.name.endswith((".yaml", ".yml")):
            data_to_validate = yaml.safe_load(content)
        else:
            data_to_validate = json.loads(content)
    elif data:
        data_to_validate = json.loads(data)
    else:
        console.print("[red]Error: Must provide --file or --data[/red]")
        sys.exit(1)

    try:
        headers = _get_headers(ctx.obj.get("config", {}))
        response = requests.post(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/schemas/{schema_name}/validate",
            headers=headers,
            json=data_to_validate,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("valid"):
            console.print("[green]✓ Validation passed[/green]")
        else:
            console.print("[red]✗ Validation failed[/red]")
            for error in result.get("errors", []):
                console.print(f"  [red]• {error}[/red]")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Schema not found: {schema_name}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schemas_group.command("example")
@click.argument("schema_name")
@click.option("--output", "-o", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def get_example(ctx: click.Context, schema_name: str, output: str):
    """Get example data for a schema"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj.get("config", {}))
        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/schemas/{schema_name}/example",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        example = response.json()

        if output == "json":
            click.echo(json.dumps(example, indent=2))
        else:
            click.echo(yaml.dump(example, default_flow_style=False))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Schema not found: {schema_name}[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Export the group
schemas_cli = schemas_group
