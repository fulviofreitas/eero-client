"""Settings commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def settings(network_id: Optional[str]):
    """Get network settings."""

    async def run_command():
        async def get_settings(client: EeroClient):
            with console.status("Getting network settings..."):
                settings_data = await client.get_settings(network_id)

            if not settings_data:
                console.print("[bold yellow]No settings data found[/bold yellow]")
                return

            # Print settings data in a formatted way
            console.print("[bold]Network Settings:[/bold]")
            for key, value in settings_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_settings)

    asyncio.run(run_command())
