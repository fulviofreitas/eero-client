"""Forwards commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def forwards(network_id: Optional[str]):
    """Get port forwards."""

    async def run_command():
        async def get_forwards(client: EeroClient):
            with console.status("Getting port forwards..."):
                forwards_data = await client.get_forwards(network_id)

            if not forwards_data:
                console.print("[bold yellow]No port forwards found[/bold yellow]")
                return

            # Print forwards data in a formatted way
            console.print("[bold]Port Forwards:[/bold]")
            for i, forward in enumerate(forwards_data, 1):
                console.print(f"[bold]Forward {i}:[/bold]")
                for key, value in forward.items():
                    console.print(f"  [dim]{key}:[/dim] {value}")
                console.print()  # Empty line between forwards

        await run_with_client(get_forwards)

    asyncio.run(run_command())
