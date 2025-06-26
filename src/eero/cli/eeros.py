"""Eero device commands for the Eero CLI."""

import asyncio
import json
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
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
def eeros(ctx: click.Context, network_id: Optional[str], output: str) -> None:
    """List all Eero devices in a network."""

    async def run_command() -> None:
        async def get_eeros(client: EeroClient) -> None:
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


def _show_eero_details(eero_id: str, network_id: Optional[str], output: str) -> None:
    """Show Eero device details (internal function)."""

    async def run_command() -> None:
        async def get_eero_details(client: EeroClient) -> None:
            with console.status("Getting Eero device details..."):
                eero = await client.get_eero(eero_id, network_id)

            if output == "json":
                console.print(eero.model_dump_json(indent=4))
            elif output == "brief":
                print_eero_details(eero)
            else:  # extensive
                print_eero_details_extensive(eero)

        await run_with_client(get_eero_details)

    asyncio.run(run_command())


@click.group(invoke_without_command=True)
@click.argument("eero-id")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def eero(ctx: click.Context, eero_id: str, network_id: Optional[str], output: str) -> None:
    """Manage a specific Eero device."""
    # Store the eero_id and network_id in the context for subcommands
    ctx.obj = {"eero_id": eero_id, "network_id": network_id, "output": output}

    # If no subcommand is specified, run the show command by default
    if ctx.invoked_subcommand is None:
        _show_eero_details(eero_id, network_id, output)


@eero.command()
@click.pass_context
def show(ctx: click.Context) -> None:
    """Show Eero device details."""
    eero_id = ctx.obj["eero_id"]
    network_id = ctx.obj["network_id"]
    output = ctx.obj["output"]
    _show_eero_details(eero_id, network_id, output)


@eero.command()
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def reboot(ctx: click.Context, force: bool) -> None:
    """Reboot an Eero device."""

    async def run_command() -> None:
        async def reboot_eero(client: EeroClient) -> None:
            eero_identifier = ctx.obj["eero_id"]
            network_id = ctx.obj["network_id"]

            try:
                # First, resolve the eero identifier to get the actual eero object
                with console.status(f"Finding Eero device '{eero_identifier}'..."):
                    eero = await client.get_eero(eero_identifier, network_id)

                # Use the resolved eero ID for the reboot operation
                resolved_eero_id = eero.eero_id
                eero_name = eero.location or eero.serial or resolved_eero_id

                if not force and not confirm_action(
                    f"Are you sure you want to reboot Eero {eero_name}?"
                ):
                    return

                with console.status("Rebooting Eero device..."):
                    result = await client.reboot_eero(resolved_eero_id, network_id)

                if result:
                    console.print(
                        f"[bold green]Reboot initiated successfully for {eero_name}[/bold green]"
                    )
                else:
                    console.print(f"[bold red]Failed to reboot Eero {eero_name}[/bold red]")

            except EeroAPIException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    # Check if this might be a feature availability issue
                    if "reboot" in str(e).lower() or "eero" in str(e).lower():
                        console.print(
                            "[bold yellow]Reboot feature is not implemented by this API/CLI[/bold yellow]"
                        )
                        console.print(
                            "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                        )
                    else:
                        console.print(
                            f"[bold yellow]Eero device '{eero_identifier}' not found[/bold yellow]"
                        )
                        console.print(
                            "[dim]Please check the device name or ID and try again.[/dim]"
                        )
                elif "403" in str(e) or "access.denied" in str(e).lower():
                    console.print(
                        "[bold yellow]Reboot feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error rebooting Eero device: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(reboot_eero)

    asyncio.run(run_command())


# Keep the old reboot command for backward compatibility
@click.command()
@click.argument("eero-id")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def reboot_standalone(eero_id: str, network_id: Optional[str]) -> None:
    """Reboot an Eero device (legacy command)."""

    async def run_command() -> None:
        async def reboot_eero(client: EeroClient) -> None:
            try:
                if not confirm_action(f"Are you sure you want to reboot Eero {eero_id}?"):
                    return

                with console.status("Rebooting Eero device..."):
                    result = await client.reboot_eero(eero_id, network_id)

                if result:
                    console.print("[bold green]Reboot initiated successfully[/bold green]")
                else:
                    console.print("[bold red]Failed to reboot Eero device[/bold red]")

            except EeroAPIException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    # Check if this might be a feature availability issue
                    if "reboot" in str(e).lower() or "eero" in str(e).lower():
                        console.print(
                            "[bold yellow]Reboot feature is not implemented by this API/CLI[/bold yellow]"
                        )
                        console.print(
                            "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                        )
                    else:
                        console.print(
                            f"[bold yellow]Eero device '{eero_id}' not found[/bold yellow]"
                        )
                        console.print(
                            "[dim]Please check the device name or ID and try again.[/dim]"
                        )
                elif "403" in str(e) or "access.denied" in str(e).lower():
                    console.print(
                        "[bold yellow]Reboot feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error rebooting Eero device: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(reboot_eero)

    asyncio.run(run_command())
