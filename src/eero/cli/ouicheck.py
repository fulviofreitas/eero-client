"""OUI Check commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def ouicheck(network_id: Optional[str]):
    """Get OUI check information."""

    async def run_command():
        async def get_ouicheck(client: EeroClient):
            with console.status("Getting OUI check information..."):
                ouicheck_data = await client.get_ouicheck(network_id)

            if not ouicheck_data:
                console.print("[bold yellow]No OUI check data found[/bold yellow]")
                return

            # Print OUI check data in a formatted way
            console.print("[bold]OUI Check:[/bold]")
            for key, value in ouicheck_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_ouicheck)

    asyncio.run(run_command())
