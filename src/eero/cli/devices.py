"""Device commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console, create_devices_table, print_device_details
from .utils import get_cookie_file, run_with_client


@click.command()
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def devices(network_id: Optional[str]):
    """List all devices in a network."""

    async def run_command():
        async def get_devices(client: EeroClient):
            with console.status("Getting devices..."):
                devices = await client.get_devices(network_id)

            if not devices:
                console.print("[bold yellow]No devices found[/bold yellow]")
                return

            table = create_devices_table(devices)
            console.print(table)

        await run_with_client(get_devices)

    asyncio.run(run_command())


@click.command()
@click.argument("device-id")
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def device(device_id: str, network_id: Optional[str]):
    """Show device details."""

    async def run_command():
        async def get_device_details(client: EeroClient):
            with console.status("Getting device details..."):
                device = await client.get_device(device_id, network_id)

            print_device_details(device)

        await run_with_client(get_device_details)

    asyncio.run(run_command())


@click.command()
@click.argument("device-id")
@click.argument("nickname")
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def rename_device(device_id: str, nickname: str, network_id: Optional[str]):
    """Set nickname for a device."""

    async def run_command():
        async def set_nickname(client: EeroClient):
            with console.status(f"Setting device nickname to '{nickname}'..."):
                result = await client.set_device_nickname(
                    device_id=device_id, nickname=nickname, network_id=network_id
                )

            if result:
                console.print(
                    "[bold green]Device nickname updated successfully[/bold green]"
                )
            else:
                console.print("[bold red]Failed to update device nickname[/bold red]")

        await run_with_client(set_nickname)

    asyncio.run(run_command())


@click.command()
@click.argument("device-id")
@click.option("--block/--unblock", required=True, help="Block or unblock the device")
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def block_device(device_id: str, block: bool, network_id: Optional[str]):
    """Block or unblock a device."""

    async def run_command():
        async def toggle_block(client: EeroClient):
            action = "Blocking" if block else "Unblocking"
            with console.status(f"{action} device..."):
                result = await client.block_device(
                    device_id=device_id, blocked=block, network_id=network_id
                )

            if result:
                status = "blocked" if block else "unblocked"
                console.print(f"[bold green]Device {status} successfully[/bold green]")
            else:
                console.print(
                    "[bold red]Failed to update device block status[/bold red]"
                )

        await run_with_client(toggle_block)

    asyncio.run(run_command())
