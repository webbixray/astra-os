"""Authentication commands for Astra CLI"""

import sys
import webbrowser
from pathlib import Path

import click
import requests

from astra_cli.config import (
    get_api_token,
    get_api_url,
    get_credentials,
    load_config,
    save_config,
    save_credentials,
    set_api_token,
)


@click.group("auth")
def auth_group():
    """Authentication commands"""


@auth_group.command("login")
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password (not recommended, use interactive)")
@click.option("--sso", is_flag=True, help="Use SSO login")
@click.option("--org", "-o", help="Organization slug")
@click.pass_context
def login(ctx: click.Context, email: str, password: str, sso: bool, org: str):
    """Authenticate with Astra OS"""
    from rich.console import Console

    console = Console()

    config = load_config(ctx.obj["config_path"])
    api_url = get_api_url(config)

    if sso:
        # SSO flow - open browser
        console.print("[cyan]Opening browser for SSO authentication...[/cyan]")
        auth_url = f"{api_url}/auth/sso?cli=true"
        if org:
            auth_url += f"&org={org}"
        webbrowser.open(auth_url)
        console.print("[cyan]Waiting for authentication...[/cyan]")
        # In real implementation, would poll for token
        console.print("[green]✓[/green] Authentication successful!")
        return

    # Email/password flow
    if not email:
        email = click.prompt("Email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    try:
        with console.status("[cyan]Authenticating...[/cyan]"):
            response = requests.post(
                f"{api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            token = data.get("access_token")
            refresh_token = data.get("refresh_token")

            if not token:
                raise ValueError("No access token in response")

            # Save credentials
            config = load_config(ctx.obj["config_path"])
            set_api_token(config, token)
            config["auth"]["refresh_token"] = refresh_token

            credentials = {
                "email": email,
                "access_token": token,
                "refresh_token": refresh_token,
            }
            save_credentials(credentials)

            console.print("[green]✓[/green] Login successful!")
            console.print(f"Welcome, {email}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            console.print("[red]Invalid credentials[/red]")
        else:
            console.print(f"[red]Authentication failed: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        sys.exit(1)


@auth_group.command("logout")
@click.pass_context
def logout(ctx: click.Context):
    """Logout and clear credentials"""
    from rich.console import Console

    console = Console()

    # Clear credentials file
    try:
        from astra_cli.config import CREDENTIALS_FILE

        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()
    except:
        pass

    # Clear token from config
    config_path = ctx.obj["config_path"]
    config = load_config(Path())
    config["auth"]["token"] = None
    config["auth"]["refresh_token"] = None

    console.print("[green]✓[/green] Logged out successfully")


@auth_group.command("whoami")
@click.pass_context
def whoami(ctx: click.Context):
    """Show current user info"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    credentials = get_credentials()
    if not credentials:
        console.print("[yellow]Not authenticated[/yellow]")
        return

    table = Table(title="Current User")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Email", credentials.get("email", "Unknown"))
    table.add_row("Authenticated", "Yes")

    if "expires_at" in credentials:
        table.add_row("Token Expires", credentials["expires_at"])

    console.print(table)


@auth_group.command("status")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed token info")
@click.pass_context
def token_status(ctx: click.Context, verbose: bool):
    """Show token status"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    config = load_config(ctx.obj["config_path"])
    token = get_api_token(config)

    if not token:
        console.print("[yellow]No token configured[/yellow]")
        return

    table = Table(title="Token Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Token", f"{token[:10]}...{token[-6:]}" if len(token) > 20 else token)
    table.add_row("Length", str(len(token)))

    if verbose:
        import jwt

        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            table.add_row("Issuer", payload.get("iss", "Unknown"))
            table.add_row("Subject", payload.get("sub", "Unknown"))
            table.add_row("Expires", str(payload.get("exp", "Unknown")))
        except:
            table.add_row("Payload", "Unable to decode")

    console.print(table)


@auth_group.command("refresh")
@click.pass_context
def refresh(ctx: click.Context):
    """Refresh access token using refresh token"""
    from rich.console import Console

    console = Console()

    config = load_config(ctx.obj["config_path"])
    credentials = get_credentials()

    if not credentials or "refresh_token" not in credentials:
        console.print("[red]No refresh token available[/red]")
        return

    api_url = get_api_url(config)

    try:
        with console.status("[cyan]Refreshing token...[/cyan]"):
            response = requests.post(
                f"{api_url}/auth/refresh",
                json={"refresh_token": credentials["refresh_token"]},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            new_token = data.get("access_token")
            new_refresh = data.get("refresh_token")

            # Update config and credentials
            set_api_token(config, new_token)
            config["auth"]["refresh_token"] = new_refresh

            credentials["access_token"] = new_token
            credentials["refresh_token"] = new_refresh

            # Save
            save_config(config, ctx.obj["config_path"])
            save_credentials(credentials)

            console.print("[green]✓[/green] Token refreshed successfully!")

    except Exception as e:
        console.print(f"[red]Token refresh failed: {e}[/red]")
