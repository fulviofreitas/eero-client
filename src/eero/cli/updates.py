"""Updates commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def updates(network_id: Optional[str]):
    """Get update information."""

    async def run_command():
        async def get_updates(client: EeroClient):
            with console.status("Getting update information..."):
                updates_data = await client.get_updates(network_id)

            if not updates_data:
                console.print("[bold yellow]No update data found[/bold yellow]")
                return

            # Print updates data in a formatted way
            console.print("[bold]Update Information:[/bold]")
            for key, value in updates_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_updates)

    asyncio.run(run_command())
