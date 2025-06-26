"""Updates commands for the Eero CLI."""

import asyncio
import json
from datetime import datetime
from typing import Optional

import click
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
from .formatting import console
from .utils import output_option, run_with_client


def format_update_status(updates_data: dict) -> None:
    """Format and display update information in a user-friendly way."""

    # Create a summary table
    table = Table(
        title="[bold blue]Eero Update Status[/bold blue]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Add key information to the table
    table.add_row("Current Firmware", updates_data.get("target_firmware", "Unknown"))
    table.add_row("Minimum Required", updates_data.get("min_required_firmware", "Unknown"))
    table.add_row(
        "Update Available", "✅ Yes" if updates_data.get("has_update", False) else "❌ No"
    )
    table.add_row(
        "Update Required", "⚠️ Yes" if updates_data.get("update_required", False) else "✅ No"
    )
    table.add_row(
        "Can Update Now", "✅ Yes" if updates_data.get("can_update_now", False) else "❌ No"
    )

    # Format preferred update hour
    preferred_hour = updates_data.get("preferred_update_hour")
    if preferred_hour is not None:
        table.add_row("Preferred Update Time", f"{preferred_hour}:00")
    else:
        table.add_row("Preferred Update Time", "Not set")

    # Format scheduled update time
    scheduled_time = updates_data.get("scheduled_update_time")
    if scheduled_time:
        try:
            dt = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))
            table.add_row("Scheduled Update", dt.strftime("%Y-%m-%d %H:%M UTC"))
        except:
            table.add_row("Scheduled Update", scheduled_time)
    else:
        table.add_row("Scheduled Update", "None")

    # Format last update time
    last_update = updates_data.get("last_update_started")
    if last_update:
        try:
            dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            table.add_row("Last Update", dt.strftime("%Y-%m-%d %H:%M UTC"))
        except:
            table.add_row("Last Update", last_update)
    else:
        table.add_row("Last Update", "Never")

    # Display the table
    console.print(table)

    # Show additional information if available
    if "last_user_update" in updates_data and updates_data["last_user_update"]:
        console.print("\n[bold yellow]Last User Update Details:[/bold yellow]")
        last_user = updates_data["last_user_update"]

        if "unresponsive_eeros" in last_user and last_user["unresponsive_eeros"]:
            console.print(
                f"  [red]Unresponsive Eeros: {len(last_user['unresponsive_eeros'])}[/red]"
            )

        if "incomplete_eeros" in last_user and last_user["incomplete_eeros"]:
            console.print(
                f"  [yellow]Incomplete Eeros: {len(last_user['incomplete_eeros'])}[/yellow]"
            )

    # Show manifest resource if available
    manifest = updates_data.get("manifest_resource")
    if manifest:
        console.print(f"\n[dim]Release Notes: {manifest}[/dim]")


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
def updates(network_id: Optional[str], output: str) -> None:
    """Get update information."""

    async def run_command() -> None:
        async def get_updates(client: EeroClient) -> None:
            try:
                with console.status("Getting update information..."):
                    updates_data = await client.get_updates(network_id)

                if not updates_data:
                    console.print("[bold yellow]No update data found[/bold yellow]")
                    return

                if output == "json":
                    console.print(json.dumps(updates_data, indent=2))
                else:
                    format_update_status(updates_data)

            except EeroAPIException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    console.print(
                        "[bold yellow]Updates feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error getting updates: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(get_updates)

    asyncio.run(run_command())
