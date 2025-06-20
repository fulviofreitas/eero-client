"""Device commands for the Eero CLI."""

import asyncio
import json
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import (
    console,
    create_devices_table,
    print_device_details,
    print_device_details_extensive,
)
from .utils import get_cookie_file, output_option, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def devices(ctx, network_id: Optional[str], output: str):
    """List all devices in a network."""

    async def run_command():
        async def get_devices(client: EeroClient):
            # Get output format from context or parameter
            output_format = (
                output
                if output != "brief"
                else (
                    ctx.parent.obj.get("output", "brief")
                    if ctx.parent and ctx.parent.obj
                    else "brief"
                )
            )

            with console.status("Getting devices..."):
                devices = await client.get_devices(network_id)

            if not devices:
                console.print("[bold yellow]No devices found[/bold yellow]")
                return

            if output_format == "json":
                if len(devices) == 1:
                    console.print(devices[0].model_dump_json(indent=4))
                else:
                    # Create a properly formatted JSON array
                    # Convert each device to dict with JSON mode to handle datetime objects
                    devices_data = [d.model_dump(mode="json") for d in devices]
                    console.print(json.dumps(devices_data, indent=4))
            else:
                table = create_devices_table(devices)
                console.print(table)

        await run_with_client(get_devices)

    asyncio.run(run_command())


@click.command()
@click.argument("device_identifier")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def device(ctx, device_identifier: str, network_id: Optional[str], output: str):
    """Show device details."""

    async def run_command():
        async def get_device_details(client: EeroClient):
            # Get output format from context or parameter
            output_format = (
                output
                if output != "brief"
                else (
                    ctx.parent.obj.get("output", "brief")
                    if ctx.parent and ctx.parent.obj
                    else "brief"
                )
            )

            nonlocal network_id
            if not network_id:
                try:
                    network = await client.get_network()
                    network_id = network.id
                except EeroException as e:
                    console.print(f"[bold red]Error: {e}[/bold red]")
                    return

            with console.status("Getting devices..."):
                devices = await client.get_devices(network_id)

            target_device = None
            for d in devices:
                if (
                    d.id == device_identifier
                    or d.display_name == device_identifier
                    or d.nickname == device_identifier
                    or d.hostname == device_identifier
                ):
                    target_device = d
                    break

            if not target_device or not target_device.id:
                console.print(f"[bold red]Device '{device_identifier}' not found[/bold red]")
                return

            with console.status("Getting device details..."):
                device_details = await client.get_device(target_device.id, network_id)

            if output_format == "brief":
                print_device_details(device_details)
            elif output_format == "extensive":
                print_device_details_extensive(device_details)
            elif output_format == "json":
                # Using .model_dump_json() for serialization
                console.print(device_details.model_dump_json(indent=4))

        await run_with_client(get_device_details)

    asyncio.run(run_command())


@click.command()
@click.argument("device-id")
@click.argument("nickname")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def rename_device(device_id: str, nickname: str, network_id: Optional[str]):
    """Set nickname for a device."""

    async def run_command():
        async def set_nickname(client: EeroClient):
            with console.status(f"Setting device nickname to '{nickname}'..."):
                result = await client.set_device_nickname(
                    device_id=device_id, nickname=nickname, network_id=network_id
                )

            if result:
                console.print("[bold green]Device nickname updated successfully[/bold green]")
            else:
                console.print("[bold red]Failed to update device nickname[/bold red]")

        await run_with_client(set_nickname)

    asyncio.run(run_command())


@click.command()
@click.argument("device-id")
@click.option("--block/--unblock", required=True, help="Block or unblock the device")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
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
                console.print("[bold red]Failed to update device block status[/bold red]")

        await run_with_client(toggle_block)

    asyncio.run(run_command())
