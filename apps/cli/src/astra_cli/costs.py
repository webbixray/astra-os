"""Cost tracking commands for Astra CLI"""

import json
import sys
from datetime import datetime, timedelta

import click
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


@click.group("costs")
def costs_group():
    """Cost tracking and reporting"""


def _get_headers(config: dict) -> dict:
    """Get API headers with auth"""
    token = config.get("auth", {}).get("token")
    if not token:
        raise click.ClickException("Not authenticated. Run 'astra auth login' first.")
    return {
        "Authorization": f"Bearer {config['auth']['token']}",
        "Content-Type": "application/json",
    }


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


@costs_group.command("report")
@click.option("--start", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end", "-e", help="End date (YYYY-MM-DD)")
@click.option("--group-by", "-g", type=click.Choice(["agent", "provider", "model", "organization", "day"]), default="agent")
@click.option("--org", "-O", help="Organization ID")
@click.option("--output", "-Q", type=click.Choice(["table", "json", "csv"]), default="table")
@click.pass_context
def cost_report(ctx: click.Context, start: str, end: str, group_by: str, org: str, output: str):
    """Generate cost report"""
    console = Console()

    # Default to last 30 days if not specified
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        headers = _get_headers(ctx.obj.get("config", {}))
        api_url = ctx.obj.get("api_url", "https://api.astra-os.io")
        params = {"start": start, "end": end, "group_by": group_by}
        if org:
            params["organization_id"] = org

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Fetching cost report...[/cyan]", total=None)

            response = requests.get(
                f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/costs/report",
                headers=_get_headers(ctx.obj.get("config", {})),
                params=params,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

        console.print(f"[bold]Cost Report: {start} to {end}[/bold]")
        console.print(f"Total Cost: [green]${data.get('total_cost', 0):,.4f}[/green]")
        console.print(f"Total Tokens: [blue]{data.get('total_tokens', 0):,}[/blue]")
        console.print()

        items = data.get("items", [])
        if not items:
            console.print("[yellow]No cost data found[/yellow]")
            return

        if output == "json":
            click.echo(json.dumps(items, indent=2))
            return
        if output == "csv":
            import csv
            import io
            output_io = io.StringIO()
            if items:
                writer = csv.DictWriter(output_io, fieldnames=items[0].keys())
                writer.writeheader()
                writer.writerows(items)
                click.echo(output_io.getvalue())
            return

        table = Table(title=f"Cost by {group_by.title()}")
        table.add_column("Category", style="cyan")
        table.add_column("Cost", style="green", justify="right")
        table.add_column("Tokens", style="blue", justify="right")
        table.add_column("Requests", style="magenta", justify="right")
        table.add_column("Avg Cost/1K Tokens", style="yellow", justify="right")

        total_cost = 0
        total_tokens = 0
        total_requests = 0

        for item in items:
            cost = item.get("cost", 0)
            tokens = item.get("tokens", 0)
            requests = item.get("requests", 0)

            avg_cost = (cost / (tokens / 1000)) if tokens > 0 else 0

            table.add_row(
                item.get("category", "Unknown"),
                f"${cost:,.4f}",
                f"{tokens:,}",
                f"{requests:,}",
                f"${avg_cost:.4f}",
            )

            total_cost += cost
            total_tokens += tokens
            total_requests += requests

        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]${total_cost:,.4f}[/bold]",
            f"[bold]{total_tokens:,}[/bold]",
            f"[bold]{total_requests:,}[/bold]",
            f"[bold]${(total_cost / (total_tokens / 1000)) if total_tokens > 0 else 0:.4f}[/bold]",
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


@costs_group.command("forecast")
@click.option("--days", "-D", default=30, help="Days to forecast")
@click.option("--org", "-O", help="Organization ID")
@click.pass_context
def cost_forecast(ctx: click.Context, days: int, org: str):
    """Forecast future costs based on current trends"""
    console = Console()

    try:
        params = {"days": days}
        if org:
            params["organization_id"] = org

        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/costs/forecast",
            headers=_get_headers(ctx.obj.get("config", {})),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        forecast = data.get("forecast", [])
        if not forecast:
            console.print("[yellow]Insufficient data for forecast[/yellow]")
            return

        table = Table(title=f"Cost Forecast ({days} days)")
        table.add_column("Date", style="cyan")
        table.add_column("Projected Cost", style="green", justify="right")
        table.add_column("Projected Tokens", style="blue", justify="right")
        table.add_column("Confidence", style="yellow", justify="right")

        for item in forecast:
            table.add_row(
                item.get("date", "N/A"),
                f"${item.get('projected_cost', 0):,.4f}",
                f"{item.get('projected_tokens', 0):,}",
                f"{item.get('confidence', 0)*100:.0f}%",
            )

        console.print(table)

        total_projected = sum(f.get("projected_cost", 0) for f in forecast)
        console.print(f"\n[bold]Total Projected: ${total_projected:,.4f}[/bold]")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            console.print("[red]Authentication failed[/red]")
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@costs_group.command("breakdown")
@click.option("--by", "-b", type=click.Choice(["provider", "model", "agent", "organization"]), default="provider")
@click.option("--start", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end", "-e", help="End date (YYYY-MM-DD)")
@click.pass_context
def cost_breakdown(ctx: click.Context, by: str, start: str, end: str):
    """Show cost breakdown by category"""
    console = Console()

    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        response = requests.get(
            f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/costs/breakdown",
            headers=_get_headers(ctx.obj.get("config", {})),
            params={"by": by, "start": start, "end": end},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        console.print(f"[bold]Cost Breakdown by {by.title()} ({start} to {end})[/bold]")
        console.print(f"Total: [green]${data.get('total', 0):,.4f}[/green]")
        console.print()

        items = data.get("breakdown", [])
        if not items:
            console.print("[yellow]No data available[/yellow]")
            return

        table = Table(title=f"Cost by {by.title()}")
        table.add_column("Category", style="cyan")
        table.add_column("Cost", style="green", justify="right")
        table.add_column("Tokens", style="blue", justify="right")
        table.add_column("Requests", style="magenta", justify="right")
        table.add_column("% of Total", style="yellow", justify="right")

        total_cost = data.get("total", 0)
        for item in items:
            cost = item.get("cost", 0)
            pct = (cost / total_cost * 100) if total_cost > 0 else 0
            table.add_row(
                item.get("category", "Unknown"),
                f"${cost:,.4f}",
                f"{item.get('tokens', 0):,}",
                f"{item.get('requests', 0):,}",
                f"{pct:.1f}%",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@costs_group.command("budget")
@click.option("--set", "budget_amount", type=float, help="Set monthly budget")
@click.option("--org", "-o", help="Organization ID")
@click.option("--alert-threshold", type=float, default=80, help="Alert at % of budget")
@click.pass_context
def cost_budget(ctx: click.Context, budget_amount: float | None, org: str, alert_threshold: float):
    """Manage cost budgets"""
    console = Console()

    try:
        if budget_amount is not None:
            # Set budget
            response = requests.post(
                f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/costs/budget",
                headers=_get_headers(ctx.obj.get("config", {})),
                json={"amount": budget_amount, "organization_id": org, "alert_threshold": alert_threshold},
                timeout=30,
            )
            response.raise_for_status()
            console.print(f"[green]✓[/green] Budget set to ${budget_amount:,.2f}/month")
        else:
            # Show current budget
            response = requests.get(
                f"{ctx.obj.get('api_url', 'https://api.astra-os.io')}/api/v1/costs/budget",
                headers=_get_headers(ctx.obj.get("config", {})),
                params={"organization_id": org} if org else {},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            budget = data.get("budget", 0)
            spent = data.get("spent", 0)
            threshold = data.get("alert_threshold", 80)
            pct = (spent / budget * 100) if budget > 0 else 0

            table = Table(title="Monthly Budget")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Budget", f"${budget:,.2f}")
            table.add_row("Spent", f"${spent:,.2f}")
            table.add_row("Remaining", f"${budget - spent:,.2f}")
            table.add_row("Usage", f"{pct:.1f}%")
            table.add_row("Alert Threshold", f"{threshold}%")

            console.print(table)

            if pct >= threshold:
                console.print(f"[red]⚠ Budget alert threshold ({threshold}%) exceeded![/red]")
            elif pct >= threshold * 0.8:
                console.print(f"[yellow]⚠ Approaching budget threshold ({threshold}%)[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Export the group
costs_cli = costs_group
