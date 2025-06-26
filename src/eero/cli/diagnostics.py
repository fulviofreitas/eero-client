"""Diagnostics commands for the Eero CLI."""

import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..client import EeroClient
from ..exceptions import EeroException
from ..models.diagnostics import DiagnosticsResult, DiagnosticsStatus
from .formatting import console
from .utils import get_cookie_file, run_with_client


def format_diagnostics_data(data: dict) -> None:
    """Format and display diagnostics data using Rich."""
    if not data:
        console.print("[bold yellow]No diagnostics data found[/bold yellow]")
        return

    # Create a table for better formatting
    table = Table(title="Network Diagnostics", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Add status with color coding
    status = data.get("status", "unknown")
    status_text = Text(status)
    if status == DiagnosticsStatus.COMPLETED:
        status_text.stylize("bold green")
    elif status == DiagnosticsStatus.IN_PROGRESS:
        status_text.stylize("bold yellow")
    elif status == DiagnosticsStatus.FAILED:
        status_text.stylize("bold red")
    else:
        status_text.stylize("bold blue")

    table.add_row("Status", status_text)

    # Add other properties
    for key, value in data.items():
        if key == "status":
            continue  # Already handled above

        if isinstance(value, dict):
            # For nested dictionaries, format them nicely
            formatted_value = "\n".join([f"  {k}: {v}" for k, v in value.items()])
            table.add_row(key.title(), formatted_value)
        elif isinstance(value, list):
            # For lists, join with commas
            formatted_value = ", ".join(str(item) for item in value)
            table.add_row(key.title(), formatted_value)
        else:
            table.add_row(key.title(), str(value))

    console.print(table)


@click.command(hidden=True)
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@click.option("--run", is_flag=True, help="Run new diagnostics instead of getting current status")
@click.option("--wait", is_flag=True, help="Wait for diagnostics to complete (only with --run)")
def diagnostics(network_id: Optional[str], run: bool, wait: bool) -> None:
    """Get or run network diagnostics information."""

    async def run_command() -> None:
        async def get_diagnostics(client: EeroClient) -> None:
            if run:
                with console.status("[bold green]Running network diagnostics..."):
                    try:
                        diagnostics_data = await client.run_diagnostics(network_id)
                        console.print(
                            "[bold green]✓[/bold green] Diagnostics started successfully!"
                        )

                        if wait:
                            console.print("[yellow]Waiting for diagnostics to complete...[/yellow]")
                            # Poll for completion
                            import time

                            max_attempts = 30  # 5 minutes max
                            for attempt in range(max_attempts):
                                await asyncio.sleep(10)  # Wait 10 seconds between checks
                                current_data = await client.get_diagnostics(network_id)
                                status = current_data.get("status", "unknown")

                                if status == DiagnosticsStatus.COMPLETED:
                                    console.print(
                                        "[bold green]✓[/bold green] Diagnostics completed!"
                                    )
                                    format_diagnostics_data(current_data)
                                    return
                                elif status == DiagnosticsStatus.FAILED:
                                    console.print("[bold red]✗[/bold red] Diagnostics failed!")
                                    format_diagnostics_data(current_data)
                                    return
                                else:
                                    console.print(f"[yellow]Status: {status}...[/yellow]")

                            console.print(
                                "[yellow]Timeout waiting for diagnostics to complete[/yellow]"
                            )
                            format_diagnostics_data(await client.get_diagnostics(network_id))
                        else:
                            format_diagnostics_data(diagnostics_data)

                    except EeroException as e:
                        console.print(f"[bold red]Error running diagnostics:[/bold red] {e}")
                        return
            else:
                with console.status("[bold blue]Getting network diagnostics..."):
                    diagnostics_data = await client.get_diagnostics(network_id)

                format_diagnostics_data(diagnostics_data)

        await run_with_client(get_diagnostics)

    asyncio.run(run_command())
