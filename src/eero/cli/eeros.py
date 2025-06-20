"""Eero device commands for the Eero CLI."""

import asyncio
import json
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import (
    console,
    create_eeros_table,
    print_eero_details,
    print_eero_details_extensive,
)
from .utils import confirm_action, get_cookie_file, output_option, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def eeros(ctx, network_id: Optional[str], output: str):
    """List all Eero devices in a network."""

    async def run_command():
        async def get_eeros(client: EeroClient):
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

            with console.status("Getting Eero devices..."):
                eeros = await client.get_eeros(network_id)

            if not eeros:
                console.print("[bold yellow]No Eero devices found[/bold yellow]")
                return

            if output_format == "json":
                if len(eeros) == 1:
                    console.print(eeros[0].model_dump_json(indent=4))
                else:
                    # Create a properly formatted JSON array
                    # Convert each eero to dict with JSON mode to handle datetime objects
                    eeros_data = [e.model_dump(mode="json") for e in eeros]
                    console.print(json.dumps(eeros_data, indent=4))
            else:
                table = create_eeros_table(eeros)
                console.print(table)

        await run_with_client(get_eeros)

    asyncio.run(run_command())


@click.command()
@click.argument("eero-id")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def eero(ctx, eero_id: str, network_id: Optional[str], output: str):
    """Show Eero device details."""

    async def run_command():
        async def get_eero_details(client: EeroClient):
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

            with console.status("Getting Eero device details..."):
                eero = await client.get_eero(eero_id, network_id)

            if output_format == "json":
                console.print(eero.model_dump_json(indent=4))
            elif output_format == "brief":
                print_eero_details(eero)
            else:  # extensive
                print_eero_details_extensive(eero)

        await run_with_client(get_eero_details)

    asyncio.run(run_command())


@click.command()
@click.argument("eero-id")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def reboot(eero_id: str, network_id: Optional[str]):
    """Reboot an Eero device."""

    async def run_command():
        async def reboot_eero(client: EeroClient):
            if not confirm_action(f"Are you sure you want to reboot Eero {eero_id}?"):
                return

            with console.status("Rebooting Eero device..."):
                result = await client.reboot_eero(eero_id, network_id)

            if result:
                console.print("[bold green]Reboot initiated successfully[/bold green]")
            else:
                console.print("[bold red]Failed to reboot Eero device[/bold red]")

        await run_with_client(reboot_eero)

    asyncio.run(run_command())
