"""AC Compatibility commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command(hidden=True)
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def ac_compat(network_id: Optional[str]) -> None:
    """Get AC compatibility information."""

    async def run_command():
        async def get_ac_compat(client: EeroClient):
            with console.status("Getting AC compatibility information..."):
                ac_compat_data = await client.get_ac_compat(network_id)

            if not ac_compat_data:
                console.print("[bold yellow]No AC compatibility data found[/bold yellow]")
                return

            # Print AC compatibility data in a formatted way
            console.print("[bold]AC Compatibility:[/bold]")
            for key, value in ac_compat_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_ac_compat)

    asyncio.run(run_command())
