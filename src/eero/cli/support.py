"""Support commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def support(network_id: Optional[str]):
    """Get network support information."""

    async def run_command():
        async def get_support(client: EeroClient):
            with console.status("Getting network support information..."):
                support_data = await client.get_support(network_id)

            if not support_data:
                console.print("[bold yellow]No support data found[/bold yellow]")
                return

            # Print support data in a formatted way
            console.print("[bold]Network Support:[/bold]")
            for key, value in support_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_support)

    asyncio.run(run_command())
