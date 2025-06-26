"""Reservations commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def reservations(network_id: Optional[str]):
    """Get DHCP reservations."""

    async def run_command():
        async def get_reservations(client: EeroClient):
            with console.status("Getting DHCP reservations..."):
                reservations_data = await client.get_reservations(network_id)

            if not reservations_data:
                console.print("[bold yellow]No DHCP reservations found[/bold yellow]")
                return

            # Print reservations data in a formatted way
            console.print("[bold]DHCP Reservations:[/bold]")
            for i, reservation in enumerate(reservations_data, 1):
                console.print(f"[bold]Reservation {i}:[/bold]")
                for key, value in reservation.items():
                    console.print(f"  [dim]{key}:[/dim] {value}")
                console.print()  # Empty line between reservations

        await run_with_client(get_reservations)

    asyncio.run(run_command())
