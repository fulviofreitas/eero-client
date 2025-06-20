"""Network commands for the Eero CLI."""

import asyncio
import json
import os
from typing import Optional

import click
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import (
    console,
    create_network_table,
    print_network_details,
    print_network_details_extensive,
)
from .utils import get_cookie_file, output_option, run_with_client, set_preferred_network


@click.command()
@output_option
@click.pass_context
def networks(ctx, output: str):
    """List all networks."""

    async def run_command():
        async def get_networks(client: EeroClient):
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

            with console.status("Getting networks..."):
                try:
                    networks = await client.get_networks()

                    if not networks:
                        # Instead of just showing an error, check if we have a preferred network ID
                        preferred_network_id = client._api.auth.preferred_network_id
                        if preferred_network_id:
                            console.print(
                                f"[bold yellow]No networks found in list, but using preferred network ID: {preferred_network_id}[/bold yellow]"
                            )
                            # Try to get details for this network
                            try:
                                network = await client.get_network(preferred_network_id)
                                if output_format == "json":
                                    console.print(network.model_dump_json(indent=4))
                                else:
                                    table = create_network_table([network])
                                    console.print(table)
                                return
                            except Exception as e:
                                console.print(
                                    f"[bold red]Error getting network details: {e}[/bold red]"
                                )

                        console.print("[bold yellow]No networks found[/bold yellow]")
                        console.print("To manually set a network ID, use:")
                        console.print("  eero set-network YOUR_NETWORK_ID")
                        return

                    if output_format == "json":
                        console.print(
                            networks[0].model_dump_json(indent=4)
                            if len(networks) == 1
                            else f"[{','.join(n.model_dump_json() for n in networks)}]"
                        )
                    else:
                        table = create_network_table(networks)
                        console.print(table)
                except Exception as e:
                    console.print(f"[bold red]Error getting networks: {e}[/bold red]")
                    console.print(
                        "[bold yellow]If you know your network ID, you can set it manually:[/bold yellow]"
                    )
                    console.print("  eero set-network YOUR_NETWORK_ID")

        await run_with_client(get_networks)

    asyncio.run(run_command())


@click.command()
@click.argument("network-id", required=False)
@output_option
@click.pass_context
def network(ctx, network_id: Optional[str], output: str):
    """Show network details."""

    async def run_command():
        async def get_network_details(client: EeroClient):
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

            with console.status("Getting network details..."):
                try:
                    network = await client.get_network(network_id)

                    if output_format == "json":
                        console.print(network.model_dump_json(indent=4))
                    elif output_format == "brief":
                        print_network_details(network)
                    else:  # extensive
                        print_network_details_extensive(network)

                except Exception as e:
                    console.print(f"[bold red]Error getting network details: {e}[/bold red]")

                    # If we have a network ID, suggest setting it manually
                    if network_id:
                        console.print(
                            f"[bold yellow]Try manually setting the network ID:[/bold yellow]"
                        )
                        console.print(f"  eero set-network {network_id}")
                    else:
                        preferred_id = client._api.auth.preferred_network_id
                        if preferred_id:
                            console.print(
                                f"[bold yellow]Using preferred network ID: {preferred_id}[/bold yellow]"
                            )
                            console.print(f"If this ID is incorrect, set it manually:")
                            console.print(f"  eero set-network YOUR_NETWORK_ID")

        await run_with_client(get_network_details)

    asyncio.run(run_command())


@click.command()
@click.argument("network-id")
def set_network(network_id: str):
    """Set preferred network for future commands."""

    async def run_command():
        async def set_preferred(client: EeroClient):
            # Set the preferred network
            client.set_preferred_network(network_id)

            # Save to config
            set_preferred_network(network_id)

            # Try to verify the network by getting its details
            try:
                with console.status(f"Verifying network ID {network_id}..."):
                    network = await client.get_network(network_id)
                network_name = network.name
                console.print(
                    f"[bold green]Preferred network set to '{network_name}' (ID: {network_id})[/bold green]"
                )
            except Exception as e:
                # Even if verification fails, we still set the network ID
                console.print(
                    f"[bold yellow]Preferred network ID set to {network_id}, but could not verify it: {e}[/bold yellow]"
                )
                console.print(
                    "[bold yellow]The ID will be used for future commands, but it may not be valid.[/bold yellow]"
                )

        await run_with_client(set_preferred)

    asyncio.run(run_command())
