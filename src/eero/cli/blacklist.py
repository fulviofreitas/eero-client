"""Blacklist commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def blacklist(network_id: Optional[str]):
    """Get device blacklist."""

    async def run_command():
        async def get_blacklist(client: EeroClient):
            with console.status("Getting device blacklist..."):
                blacklist_data = await client.get_blacklist(network_id)

            if not blacklist_data:
                console.print("[bold yellow]No blacklisted devices found[/bold yellow]")
                return

            # Print blacklist data in a formatted way
            console.print("[bold]Device Blacklist:[/bold]")
            for i, device in enumerate(blacklist_data, 1):
                console.print(f"[bold]Device {i}:[/bold]")
                for key, value in device.items():
                    console.print(f"  [dim]{key}:[/dim] {value}")
                console.print()  # Empty line between devices

        await run_with_client(get_blacklist)

    asyncio.run(run_command())
