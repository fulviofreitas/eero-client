"""Thread commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def thread(network_id: Optional[str]):
    """Get network thread information."""

    async def run_command():
        async def get_thread(client: EeroClient):
            with console.status("Getting network thread information..."):
                thread_data = await client.get_thread(network_id)

            if not thread_data:
                console.print("[bold yellow]No thread data found[/bold yellow]")
                return

            # Print thread data in a formatted way
            console.print("[bold]Network Thread:[/bold]")
            for key, value in thread_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_thread)

    asyncio.run(run_command())
