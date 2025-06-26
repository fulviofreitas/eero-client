"""Thread commands for the Eero CLI."""

import asyncio
from typing import Optional

import click
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console
from .utils import run_with_client


def print_thread_brief(thread_data: dict) -> None:
    """Print thread information in brief format."""
    table = Table(title="Network Thread", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Status", style="yellow")

    # Basic thread info
    enabled = thread_data.get("enabled", False)
    status = "🟢 Enabled" if enabled else "🔴 Disabled"
    table.add_row("Status", "Thread Network", status)

    name = thread_data.get("name", "N/A")
    table.add_row("Network Name", name, "")

    xpan_id = thread_data.get("xpan_id", "N/A")
    table.add_row("XPAN ID", xpan_id, "")

    pan_id = thread_data.get("pan_id", "N/A")
    table.add_row("PAN ID", pan_id, "")

    channel = thread_data.get("channel", "N/A")
    table.add_row("Channel", str(channel), "")

    # Border agent info
    border_agent = thread_data.get("border_agent", {})
    if border_agent:
        ip = border_agent.get("ip", "N/A")
        port = border_agent.get("port", "N/A")
        table.add_row("Border Agent", f"{ip}:{port}", "Active" if ip != "N/A" else "None")

    console.print(table)


def print_thread_extensive(thread_data: dict) -> None:
    """Print thread information in extensive format."""
    console.print("[bold blue]Network Thread Information[/bold blue]")
    console.print()

    # Main thread table
    table = Table(title="Thread Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Description", style="dim")

    # Basic configuration
    enabled = thread_data.get("enabled", False)
    status_emoji = "🟢" if enabled else "🔴"
    table.add_row(
        "Status", f"{status_emoji} {'Enabled' if enabled else 'Disabled'}", "Thread network status"
    )

    name = thread_data.get("name", "N/A")
    table.add_row("Network Name", name, "Thread network identifier")

    xpan_id = thread_data.get("xpan_id", "N/A")
    table.add_row("XPAN ID", xpan_id, "Extended PAN identifier")

    pan_id = thread_data.get("pan_id", "N/A")
    table.add_row("PAN ID", pan_id, "Personal Area Network ID")

    channel = thread_data.get("channel", "N/A")
    table.add_row("Channel", str(channel), "Thread network channel")

    enable_credential_syncing = thread_data.get("enable_credential_syncing", False)
    sync_emoji = "🟢" if enable_credential_syncing else "🔴"
    table.add_row(
        "Credential Syncing",
        f"{sync_emoji} {'Enabled' if enable_credential_syncing else 'Disabled'}",
        "Credential synchronization",
    )

    console.print(table)
    console.print()

    # Security information
    console.print("[bold green]🔐 Security Information[/bold green]")
    security_table = Table(show_header=True, header_style="bold green")
    security_table.add_column("Security Element", style="cyan")
    security_table.add_column("Value", style="white")
    security_table.add_column("Description", style="dim")

    master_key = thread_data.get("master_key", "N/A")
    security_table.add_row("Master Key", master_key, "Thread network master key")

    commissioning_credential = thread_data.get("commissioning_credential", "N/A")
    security_table.add_row(
        "Commissioning Credential", commissioning_credential, "Device commissioning password"
    )

    console.print(security_table)
    console.print()

    # Border agent information
    border_agent = thread_data.get("border_agent", {})
    if border_agent:
        console.print("[bold yellow]🌐 Border Agent[/bold yellow]")
        border_table = Table(show_header=True, header_style="bold yellow")
        border_table.add_column("Property", style="cyan")
        border_table.add_column("Value", style="white")
        border_table.add_column("Description", style="dim")

        ip = border_agent.get("ip", "N/A")
        port = border_agent.get("port", "N/A")
        border_table.add_row("IP Address", ip, "Border agent IP address")
        border_table.add_row("Port", str(port), "Border agent port number")
        border_table.add_row("Endpoint", f"{ip}:{port}", "Full border agent endpoint")

        console.print(border_table)
        console.print()

    # API endpoint information
    console.print("[bold purple]🔗 API Information[/bold purple]")
    api_table = Table(show_header=True, header_style="bold purple")
    api_table.add_column("Property", style="cyan")
    api_table.add_column("Value", style="white")

    url = thread_data.get("url", "N/A")
    api_table.add_row("API Endpoint", url)

    console.print(api_table)


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@click.option(
    "--output",
    type=click.Choice(["brief", "extensive", "json"]),
    default="brief",
    help="Output format",
)
def thread(network_id: Optional[str], output: str) -> None:
    """Get network thread information."""

    async def run_command() -> None:
        async def get_thread(client: EeroClient) -> None:
            with console.status("Getting network thread information..."):
                thread_data = await client.get_thread(network_id)

            if not thread_data:
                console.print("[bold yellow]No thread data found[/bold yellow]")
                return

            if output == "json":
                console.print_json(data=thread_data)
            elif output == "brief":
                print_thread_brief(thread_data)
            else:  # extensive
                print_thread_extensive(thread_data)

        await run_with_client(get_thread)

    asyncio.run(run_command())
