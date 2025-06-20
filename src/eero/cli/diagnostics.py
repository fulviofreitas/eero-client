"""Diagnostics commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import get_cookie_file, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def diagnostics(network_id: Optional[str]):
    """Get network diagnostics information."""

    async def run_command():
        async def get_diagnostics(client: EeroClient):
            with console.status("Getting network diagnostics..."):
                diagnostics_data = await client.get_diagnostics(network_id)

            if not diagnostics_data:
                console.print("[bold yellow]No diagnostics data found[/bold yellow]")
                return

            # Print diagnostics data in a formatted way
            console.print("[bold]Network Diagnostics:[/bold]")
            for key, value in diagnostics_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_diagnostics)

    asyncio.run(run_command())
