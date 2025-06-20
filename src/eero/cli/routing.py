"""Routing commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def routing(network_id: Optional[str]):
    """Get network routing information."""

    async def run_command():
        async def get_routing(client: EeroClient):
            with console.status("Getting network routing information..."):
                routing_data = await client.get_routing(network_id)

            if not routing_data:
                console.print("[bold yellow]No routing data found[/bold yellow]")
                return

            # Print routing data in a formatted way
            console.print("[bold]Network Routing:[/bold]")
            for key, value in routing_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_routing)

    asyncio.run(run_command())
