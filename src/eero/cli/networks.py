"""Network commands for the Eero CLI."""

import asyncio
from typing import Optional

import click
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console, create_network_table, print_network_details
from .utils import get_cookie_file, run_with_client, set_preferred_network


@click.command()
def networks():
    """List all networks."""

    async def run_command():
        async def get_networks(client: EeroClient):
            with console.status("Getting networks..."):
                networks = await client.get_networks()

            if not networks:
                console.print("[bold yellow]No networks found[/bold yellow]")
                return

            table = create_network_table(networks)
            console.print(table)

        await run_with_client(get_networks)

    asyncio.run(run_command())


@click.command()
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def network(network_id: Optional[str]):
    """Show network details."""

    async def run_command():
        async def get_network_details(client: EeroClient):
            with console.status("Getting network details..."):
                network = await client.get_network(network_id)

            print_network_details(network)

        await run_with_client(get_network_details)

    asyncio.run(run_command())


@click.command()
@click.argument("network-id")
def set_network(network_id: str):
    """Set preferred network for future commands."""

    async def run_command():
        async def set_preferred(client: EeroClient):
            # Verify the network exists
            with console.status("Verifying network..."):
                networks = await client.get_networks()
                network_ids = [net.id for net in networks]

                if network_id not in network_ids:
                    console.print(
                        f"[bold red]Network ID {network_id} not found[/bold red]"
                    )
                    return

                # Set the preferred network
                client.set_preferred_network(network_id)

                # Save to config
                set_preferred_network(network_id)

                # Get the network name for the success message
                network_name = next(
                    net.name for net in networks if net.id == network_id
                )
                console.print(
                    f"[bold green]Preferred network set to '{network_name}'[/bold green]"
                )

        await run_with_client(set_preferred)

    asyncio.run(run_command())
