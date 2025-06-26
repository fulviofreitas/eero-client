"""Routing commands for the Eero CLI."""

import asyncio
from typing import Optional

import click
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


def print_routing_brief(routing_data: dict) -> None:
    """Print routing information in brief format."""
    table = Table(title="Network Routing", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Count", style="green", justify="right")
    table.add_column("Details", style="white")

    # Count devices
    devices_count = len(routing_data.get("devices", {}).get("data", []))
    table.add_row("Devices", str(devices_count), f"Total connected devices")

    # Count reservations
    reservations_count = len(routing_data.get("reservations", {}).get("data", []))
    table.add_row("Reservations", str(reservations_count), f"IP reservations")

    # Count forwards
    forwards_count = len(routing_data.get("forwards", {}).get("data", []))
    table.add_row("Port Forwards", str(forwards_count), f"Port forwarding rules")

    # Count pinholes
    pinholes_count = len(routing_data.get("pinholes", {}).get("data", []))
    table.add_row("IPv6 Pinholes", str(pinholes_count), f"IPv6 pinhole rules")

    console.print(table)


def print_routing_extensive(routing_data: dict) -> None:
    """Print routing information in extensive format."""
    console.print("[bold blue]Network Routing Information[/bold blue]")
    console.print()

    # Create main routing table
    table = Table(title="Routing Components", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("URL", style="dim")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Status", style="yellow")

    # Devices section
    devices = routing_data.get("devices", {})
    devices_count = len(devices.get("data", []))
    devices_url = devices.get("url", "N/A")
    table.add_row(
        "📱 Connected Devices",
        devices_url,
        str(devices_count),
        "Active" if devices_count > 0 else "None",
    )

    # Reservations section
    reservations = routing_data.get("reservations", {})
    reservations_count = len(reservations.get("data", []))
    reservations_url = reservations.get("url", "N/A")
    table.add_row(
        "🔒 IP Reservations",
        reservations_url,
        str(reservations_count),
        "Active" if reservations_count > 0 else "None",
    )

    # Forwards section
    forwards = routing_data.get("forwards", {})
    forwards_count = len(forwards.get("data", []))
    forwards_url = forwards.get("url", "N/A")
    table.add_row(
        "🔀 Port Forwards",
        forwards_url,
        str(forwards_count),
        "Active" if forwards_count > 0 else "None",
    )

    # Pinholes section
    pinholes = routing_data.get("pinholes", {})
    pinholes_count = len(pinholes.get("data", []))
    pinholes_url = pinholes.get("url", "N/A")
    table.add_row(
        "🔓 IPv6 Pinholes",
        pinholes_url,
        str(pinholes_count),
        "Active" if pinholes_count > 0 else "None",
    )

    console.print(table)
    console.print()

    # Show all devices if any exist
    device_data = devices.get("data", [])
    if device_data:
        console.print(f"[bold cyan]All Connected Devices ({len(device_data)})[/bold cyan]")
        device_table = Table(show_header=True, header_style="bold cyan")
        device_table.add_column("Nickname", style="white")
        device_table.add_column("MAC Address", style="dim")
        device_table.add_column("Device ID", style="green")

        # Show all devices
        for device in device_data:
            nickname = device.get("nickname", "Unnamed")
            mac = device.get("mac", "Unknown")
            device_id = device.get("url", "").split("/")[-1] if device.get("url") else "Unknown"
            device_table.add_row(nickname, mac, device_id)

        console.print(device_table)
        console.print()

    # Show all reservations if any exist
    reservations_data = reservations.get("data", [])
    if reservations_data:
        console.print(f"[bold green]All IP Reservations ({len(reservations_data)})[/bold green]")
        reservation_table = Table(show_header=True, header_style="bold green")
        reservation_table.add_column("Reservation", style="white")

        for reservation in reservations_data:
            reservation_table.add_row(str(reservation))

        console.print(reservation_table)
        console.print()

    # Show all forwards if any exist
    forwards_data = forwards.get("data", [])
    if forwards_data:
        console.print(f"[bold yellow]All Port Forwards ({len(forwards_data)})[/bold yellow]")
        forward_table = Table(show_header=True, header_style="bold yellow")
        forward_table.add_column("Forward Rule", style="white")

        for forward in forwards_data:
            forward_table.add_row(str(forward))

        console.print(forward_table)
        console.print()

    # Show all pinholes if any exist
    pinholes_data = pinholes.get("data", [])
    if pinholes_data:
        console.print(f"[bold purple]All IPv6 Pinholes ({len(pinholes_data)})[/bold purple]")
        pinhole_table = Table(show_header=True, header_style="bold purple")
        pinhole_table.add_column("Pinhole Rule", style="white")

        for pinhole in pinholes_data:
            pinhole_table.add_row(str(pinhole))

        console.print(pinhole_table)


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@click.option(
    "--output",
    type=click.Choice(["brief", "extensive", "json"]),
    default="brief",
    help="Output format",
)
def routing(network_id: Optional[str], output: str) -> None:
    """Get network routing information."""

    async def run_command() -> None:
        async def get_routing(client: EeroClient) -> None:
            with console.status("Getting network routing information..."):
                routing_data = await client.get_routing(network_id)

            if not routing_data:
                console.print("[bold yellow]No routing data found[/bold yellow]")
                return

            if output == "json":
                console.print_json(data=routing_data)
            elif output == "brief":
                print_routing_brief(routing_data)
            else:  # extensive
                print_routing_extensive(routing_data)

        await run_with_client(get_routing)

    asyncio.run(run_command())
