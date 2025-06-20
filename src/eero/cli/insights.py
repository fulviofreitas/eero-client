"""Insights commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def insights(network_id: Optional[str]):
    """Get network insights."""

    async def run_command():
        async def get_insights(client: EeroClient):
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

        await run_with_client(get_insights)

    asyncio.run(run_command())
