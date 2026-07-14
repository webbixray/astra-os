#!/usr/bin/env python3
"""Astra OS CLI - Main Entry Point"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from astra_cli.agents import agents_cli
from astra_cli.auth import login, logout, token_status, whoami
from astra_cli.config import get_config_value, load_config, save_config, set_config_value
from astra_cli.costs import costs_cli
from astra_cli.monitoring import monitoring_cli
from astra_cli.schemas import schemas_cli
from astra_cli.workflows import workflows_cli

console = Console()

# Global config path
CONFIG_DIR = Path.home() / ".astra"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.yaml"


@click.group()
@click.version_option(version="0.1.0", prog_name="astra")
@click.option(
    "--config", "-c",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default=CONFIG_FILE,
    help="Path to config file",
)
@click.option(
    "--verbose", "-v",
    count=True,
    help="Increase verbosity",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["table", "json", "yaml", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(ctx: click.Context, config: Path, verbose: int, output: str):
    """Astra OS CLI - AI-Native Marketing & Business Growth Operating System"""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["output_format"] = output

    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


@cli.command()
@click.pass_context
def init(ctx: click.Context):
    """Initialize Astra CLI configuration"""
    config_path = ctx.obj["config_path"]

    if config_path.exists():
        if not click.confirm(f"Config already exists at {config_path}. Overwrite?"):
            console.print("Initialization cancelled.")
            return

    # Create default config
    default_config = {
        "api": {
            "url": "https://api.astra-os.io",
            "timeout": 30,
        },
        "auth": {
            "token": None,
            "refresh_token": None,
        },
        "defaults": {
            "organization": None,
            "project": None,
            "output_format": "table",
        },
        "monitoring": {
            "enabled": True,
            "interval": 60,
        },
    }

    # Import here to avoid circular imports
    save_config(default_config, CONFIG_FILE)

    console.print(f"[green]✓[/green] Config created at {CONFIG_FILE}")
    console.print("\nNext steps:")
    console.print("  1. Run [bold]astra auth login[/bold] to authenticate")
    console.print("  2. Run [bold]astra config set defaults.organization <org>[/bold] to set default org")
    console.print("  4. Run [bold]astra agents list[/bold] to see available agents")


@cli.command()
@click.pass_context
def doctor(ctx: click.Context):
    """Check CLI health and configuration"""
    config_path = ctx.obj["config_path"]

    console.print("[bold]Astra CLI Health Check[/bold]\n")

    # Check config file
    if config_path.exists():
        console.print(f"[green]✓[/green] Config file: {config_path}")
    else:
        console.print(f"[red]✗[/red] Config file missing: {config_path}")

    # Check credentials
    if CREDENTIALS_FILE.exists():
        console.print(f"[green]✓[/green] Credentials file: {CREDENTIALS_FILE}")
    else:
        console.print("[yellow]![/yellow] No credentials file (run 'astra auth login')")

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"[green]✓[/green] Python: {python_version}")

    # Check dependencies
    try:
        import click
        import httpx
        import pydantic
        import rich
        import yaml
        console.print("[green]✓[/green] Core dependencies installed")
    except ImportError as e:
        console.print(f"[red]✗[/red] Missing dependency: {e}")

    # Check API connectivity (if configured)
    config = load_config(config_path)
    api_url = config.get("api", {}).get("url")
    if api_url:
        console.print(f"[green]✓[/green] API URL configured: {api_url}")
    else:
        console.print("[yellow]![/yellow] No API URL configured")

    console.print("\n[bold]Status: Healthy[/bold]" if not any([
        not config_path.exists(),
        not CREDENTIALS_FILE.exists(),
    ]) else "\n[bold]Status: Issues found[/bold]")


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), default="yaml")
@click.pass_context
def version(ctx: click.Context, fmt: str):
    """Show version information"""
    import sys

    import astra_cli

    info = {
        "astra-cli": astra_cli.__version__,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
    }

    if fmt == "json":
        import json
        console.print(json.dumps(info, indent=2))
    else:
        import yaml
        console.print(yaml.dump(info, default_flow_style=False))


# Auth subcommands
auth_group = click.Group("auth", help="Authentication commands")
auth_group.add_command(login, name="login")
auth_group.add_command(logout, name="logout")
auth_group.add_command(whoami, name="whoami")
auth_group.add_command(token_status, name="status")
cli.add_command(auth_group, name="auth")

# Config subcommands
config_group = click.Group("config", help="Configuration commands")

@config_group.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx: click.Context, key: str):
    """Get a configuration value"""
    config = load_config(ctx.obj["config_path"])
    value = get_config_value(config, key)
    if value is None:
        console.print(f"[yellow]Key not found: {key}[/yellow]")
    else:
        console.print(value)

@config_group.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str):
    """Set a configuration value"""
    config = load_config(ctx.obj["config_path"])
    set_config_value(config, key, value)
    save_config(config, ctx.obj["config_path"])
    console.print(f"[green]✓[/green] Set {key} = {value}")

@config_group.command("list")
@click.pass_context
def config_list(ctx: click.Context):
    """List all configuration values"""
    config = load_config(ctx.obj["config_path"])

    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    def flatten(d, prefix=""):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flatten(v, key)
            else:
                table.add_row(key, str(v))

    flatten(config)
    console.print(table)

cli.add_command(config_group, name="config")

# Add all command groups
cli.add_command(agents_cli, name="agents")
cli.add_command(workflows_cli, name="workflows")
cli.add_command(monitoring_cli, name="monitor")
cli.add_command(schemas_cli, name="schemas")
cli.add_command(costs_cli, name="costs")


def main():
    """Main entry point"""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
