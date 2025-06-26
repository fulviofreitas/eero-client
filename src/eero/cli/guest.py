"""Guest network commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import get_cookie_file, run_with_client


@click.command()
@click.option(
    "--enable/--disable", required=True, help="Enable or disable guest network"
)
@click.option("--name", help="Guest network name (when enabling)")
@click.option("--password", help="Guest network password (when enabling)")
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def guest_network(
    enable: bool,
    name: Optional[str],
    password: Optional[str],
    network_id: Optional[str],
):
    """Enable or disable guest network."""

    async def run_command():
        async def configure_guest_network(client: EeroClient):
            with console.status("Updating guest network..."):
                result = await client.set_guest_network(
                    enabled=enable, name=name, password=password, network_id=network_id
                )

            if result:
                status = "enabled" if enable else "disabled"
                console.print(
                    f"[bold green]Guest network {status} successfully[/bold green]"
                )
            else:
                console.print("[bold red]Failed to update guest network[/bold red]")

        await run_with_client(configure_guest_network)

    asyncio.run(run_command())
