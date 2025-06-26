"""Insights commands for the Eero CLI."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
from .formatting import console
from .utils import run_with_client


@click.command(hidden=True)
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@click.option("--start-date", help="Start date for insights (YYYY-MM-DD)")
@click.option("--end-date", help="End date for insights (YYYY-MM-DD)")
def insights(network_id: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> None:
    """Get network insights."""

    async def run_command() -> None:
        async def get_insights(client: EeroClient) -> None:
            try:
                with console.status("Getting network insights..."):
                    insights_data = await client.get_insights(network_id)

                if not insights_data:
                    console.print("[bold yellow]No insights data found[/bold yellow]")
                    return

                # Print insights data in a formatted way
                console.print("[bold]Network Insights:[/bold]")
                for key, value in insights_data.items():
                    if isinstance(value, dict):
                        console.print(f"[bold]{key}:[/bold]")
                        for sub_key, sub_value in value.items():
                            console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                    else:
                        console.print(f"[bold]{key}:[/bold] {value}")

            except EeroAPIException as e:
                if "400" in str(e) and (
                    "start" in str(e).lower()
                    or "end" in str(e).lower()
                    or "form.errors" in str(e).lower()
                ):
                    console.print(
                        "[bold yellow]Insights feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                elif "404" in str(e) or "not found" in str(e).lower():
                    console.print(
                        "[bold yellow]Insights feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error getting insights: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(get_insights)

    asyncio.run(run_command())
