"""Monitoring commands for Astra CLI"""

import json
import sys

import click
import requests
from rich.console import Console
from rich.table import Table


@click.group("monitor")
def monitoring_group():
    """Monitoring and observability commands"""


def _get_headers(config: dict) -> dict:
    """Get API headers with auth"""
    token = config.get("auth", {}).get("token")
    if not token:
        raise click.ClickException("Not authenticated. Run 'astra auth login' first.")
    return {
        "Authorization": f"Bearer {config['auth']['token']}",
        "Content-Type": "application/json",
    }


@monitoring_group.command("health")
@click.option("--service", "-s", help="Service name (api, workers, agents)")
@click.pass_context
def health_check(ctx: click.Context, service: str):
    """Check service health"""
    console = Console()

    try:
        endpoint = f"{ctx.obj['api_url']}/api/v1/health"
        if service:
            endpoint += f"/{service}"

        response = requests.get(
            endpoint,
            headers=_get_headers(ctx.obj["config"]),
            timeout=10,
        )
        response.raise_for_status()
        health = response.json()

        console.print("[green]✓[/green] Service healthy")
        if isinstance(health, dict):
            for key, value in health.items():
                console.print(f"  {key}: {value}")
        else:
            console.print(f"  {health}")

    except Exception as e:
        console.print(f"[red]Health check failed: {e}[/red]")
        sys.exit(1)


@monitoring_group.command("metrics")
@click.option("--service", "-s", help="Service name")
@click.option("--metric", "-m", help="Specific metric name")
@click.option("--duration", "-d", default="1h", help="Time range (e.g., 1h, 24h)")
@click.pass_context
def get_metrics(ctx: click.Context, service: str, metric: str, duration: str):
    """Get Prometheus metrics"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj["config"])
        params = {"duration": duration}
        if service:
            params["service"] = service
        if metric:
            params["metric"] = metric

        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/metrics",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        metrics = response.json()

        if not metrics:
            console.print("[yellow]No metrics found[/yellow]")
            return

        if isinstance(metrics, dict):
            for key, value in metrics.items():
                console.print(f"[cyan]{key}[/cyan]: {value}")
        else:
            console.print(json.dumps(metrics, indent=2))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@monitoring_group.command("alerts")
@click.option("--status", "-s", type=click.Choice(["firing", "resolved", "all"]), default="firing")
@click.option(
    "--severity", "-s", type=click.Choice(["critical", "warning", "info", "all"]), default="all"
)
@click.pass_context
def list_alerts(ctx: click.Context, status: str, severity: str):
    """List active alerts"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj["config"])
        params = {"status": status}
        if severity != "all":
            params["severity"] = severity

        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/alerts",
            headers=_get_headers(ctx.obj["config"]),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        alerts = response.json().get("alerts", [])

        if not alerts:
            console.print("[yellow]No alerts[/yellow]")
            return

        table = Table(title=f"Alerts ({len(alerts)})")
        table.add_column("Name", style="cyan")
        table.add_column("Severity", style="red")
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="dim")
        table.add_column("Summary", style="white")

        for alert in alerts:
            table.add_row(
                alert.get("name", "N/A"),
                alert.get("severity", "unknown"),
                alert.get("status", "unknown"),
                alert.get("started_at", "N/A")[:19],
                alert.get("summary", "")[:50],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@monitoring_group.command("slo")
@click.option("--name", "-n", help="SLO name")
@click.pass_context
def show_slo(ctx: click.Context, name: str):
    """Show SLO status"""
    console = Console()

    try:
        headers = _get_headers(ctx.obj["config"])
        params = {}
        if name:
            params["name"] = name

        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/slos",
            headers=_get_headers(ctx.obj["config"]),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        slos = response.json().get("slos", [])

        if not slos:
            console.print("[yellow]No SLOs found[/yellow]")
            return

        table = Table(title="SLO Status")
        table.add_column("SLO", style="cyan")
        table.add_column("Target", style="green")
        table.add_column("Current", style="yellow")
        table.add_column("Error Budget", style="red")
        table.add_column("Burn Rate", style="magenta")

        for slo in slos:
            table.add_row(
                slo.get("name", "N/A"),
                f"{slo.get('target', 0) * 100:.2f}%",
                f"{slo.get('current', 0) * 100:.2f}%",
                f"{slo.get('error_budget_remaining', 0) * 100:.2f}%",
                f"{slo.get('burn_rate', 0):.2f}x",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@monitoring_group.command("trace")
@click.argument("trace_id")
@click.option("--follow", "-f", is_flag=True, help="Follow trace updates")
@click.pass_context
def get_trace(ctx: click.Context, trace_id: str, follow: bool):
    """Get trace details"""
    console = Console()

    try:
        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/traces/{trace_id}",
            headers=_get_headers(ctx.obj["config"]),
            timeout=30,
        )
        response.raise_for_status()
        trace = response.json()

        console.print(f"Trace: {trace_id}")
        console.print(f"Duration: {trace.get('duration_ms', 0)}ms")
        console.print(f"Spans: {len(trace.get('spans', []))}")

        if trace.get("spans"):
            table = Table(title="Spans")
            table.add_column("Name", style="cyan")
            table.add_column("Kind", style="yellow")
            table.add_column("Duration", style="green")
            table.add_column("Status", style="magenta")

            for span in trace.get("spans", []):
                table.add_row(
                    span.get("name", "N/A"),
                    span.get("kind", "N/A"),
                    f"{span.get('duration_ms', 0)}ms",
                    span.get("status", "ok"),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@monitoring_group.command("circuit-breakers")
@click.pass_context
def circuit_breakers(ctx: click.Context):
    """Show circuit breaker status"""
    console = Console()

    try:
        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/circuit-breakers",
            headers=_get_headers(ctx.obj["config"]),
            timeout=30,
        )
        response.raise_for_status()
        breakers = response.json().get("breakers", [])

        if not breakers:
            console.print("[yellow]No circuit breakers[/yellow]")
            return

        table = Table(title="Circuit Breakers")
        table.add_column("Name", style="cyan")
        table.add_column("State", style="red")
        table.add_column("Failures", style="yellow")
        table.add_column("Successes", style="green")
        table.add_column("Last Failure", style="dim")

        for cb in breakers:
            state = cb.get("state", "unknown")
            state_style = (
                "green" if state == "closed" else ("yellow" if state == "half_open" else "red")
            )
            table.add_row(
                cb.get("name", "N/A"),
                f"[{state_style}]{state}[/{state_style}]",
                str(cb.get("failures", 0)),
                str(cb.get("successes", 0)),
                cb.get("last_failure", "never"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@monitoring_group.command("dlq")
@click.option("--stream", "-s", help="Stream name")
@click.pass_context
def dlq_status(ctx: click.Context, stream: str):
    """Show DLQ status"""
    console = Console()

    try:
        params = {}
        if stream:
            params["stream"] = stream

        response = requests.get(
            f"{ctx.obj['api_url']}/api/v1/dlq",
            headers=_get_headers(ctx.obj["config"]),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        console.print(f"Total DLQ messages: {data.get('total', 0)}")

        streams = data.get("streams", [])
        if not streams:
            console.print("[yellow]No DLQ messages[/yellow]")
            return

        table = Table(title="DLQ Streams")
        table.add_column("Stream", style="cyan")
        table.add_column("Messages", style="red")
        table.add_column("Oldest", style="dim")
        table.add_column("Latest", style="dim")

        for s in streams:
            table.add_row(
                s.get("stream", "N/A"),
                str(s.get("count", 0)),
                s.get("oldest", "N/A"),
                s.get("latest", "N/A"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# Group all monitoring commands
monitoring_cli = click.Group("monitor", help="Monitoring and observability commands")
monitoring_cli.add_command(health_check, name="health")
monitoring_cli.add_command(get_metrics, name="metrics")
monitoring_cli.add_command(list_alerts, name="alerts")
monitoring_cli.add_command(show_slo, name="slo")
monitoring_cli.add_command(get_trace, name="trace")
monitoring_cli.add_command(circuit_breakers, name="circuit-breakers")
monitoring_cli.add_command(dlq_status, name="dlq")
