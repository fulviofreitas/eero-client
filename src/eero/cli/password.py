"""Password commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def password(network_id: Optional[str]):
    """Get password information."""

    async def run_command():
        async def get_password(client: EeroClient):
            with console.status("Getting password information..."):
                password_data = await client.get_password(network_id)

            if not password_data:
                console.print("[bold yellow]No password data found[/bold yellow]")
                return

            # Print password data in a formatted way
            console.print("[bold]Password Information:[/bold]")
            for key, value in password_data.items():
                if isinstance(value, dict):
                    console.print(f"[bold]{key}:[/bold]")
                    for sub_key, sub_value in value.items():
                        console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                else:
                    console.print(f"[bold]{key}:[/bold] {value}")

        await run_with_client(get_password)

    asyncio.run(run_command())
