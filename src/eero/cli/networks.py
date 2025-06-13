"""Network commands for the Eero CLI."""

from typing import Optional

import typer
from rich.progress import Progress
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroException
from .utils import set_preferred_network, with_eero_client

networks_commands = typer.Typer(help="Network management commands")


@networks_commands.command(name="list")
@with_eero_client
async def list_networks(client: EeroClient):
    """List all networks."""
    ctx = typer.Context.get_current()
    console = ctx.obj["console"]

    with console.status("Getting networks..."):
        networks = await client.get_networks()

    if not networks:
        console.print("[bold yellow]No networks found[/bold yellow]")
        return

    table = Table(title="Eero Networks")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Public IP", style="blue")
    table.add_column("ISP", style="magenta")
    table.add_column("Created", style="yellow")

    for network in networks:
        status_style = "green" if network.status == "online" else "red"
        table.add_row(
            network.id,
            network.name,
            f"[{status_style}]{network.status}[/{status_style}]",
            network.public_ip or "Unknown",
            network.isp_name or "Unknown",
            (
                network.created_at.strftime("%Y-%m-%d")
                if network.created_at
                else "Unknown"
            ),
        )

    console.print(table)


@networks_commands.command(name="show")
@with_eero_client
async def show_network(
    client: EeroClient,
    network_id: Optional[str] = typer.Argument(
        None, help="Network ID (uses preferred network if not specified)"
    ),
):
    """Show network details."""
    ctx = typer.Context.get_current()
    console = ctx.obj["console"]

    with console.status("Getting network details..."):
        network = await client.get_network(network_id)

    from .formatting import print_network_details

    print_network_details(network)


@networks_commands.command(name="set-preferred")
@with_eero_client
async def set_network(
    client: EeroClient,
    network_id: str = typer.Argument(..., help="Network ID to set as preferred"),
):
    """Set preferred network for future commands."""
    ctx = typer.Context.get_current()
    console = ctx.obj["console"]

    # Verify the network exists
    with console.status("Verifying network..."):
        networks = await client.get_networks()
        network_ids = [net.id for net in networks]

        if network_id not in network_ids:
            console.print(f"[bold red]Network ID {network_id} not found[/bold red]")
            return

        # Set the preferred network
        client.set_preferred_network(network_id)

        # Save to config
        set_preferred_network(network_id)

        # Get the network name for the success message
        network_name = next(net.name for net in networks if net.id == network_id)
        console.print(
            f"[bold green]Preferred network set to '{network_name}'[/bold green]"
        )
