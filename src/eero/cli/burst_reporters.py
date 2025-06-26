"""Burst Reporters commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
from .formatting import console
from .utils import run_with_client


@click.command(hidden=True)
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def burst_reporters(network_id: Optional[str]) -> None:
    """Get burst reporters."""

    async def run_command() -> None:
        async def get_burst_reporters(client: EeroClient) -> None:
            try:
                with console.status("Getting burst reporters..."):
                    reporters_data = await client.get_burst_reporters(network_id)

                if not reporters_data:
                    console.print("[bold yellow]No burst reporters found[/bold yellow]")
                    return

                # Print reporters data in a formatted way
                console.print("[bold]Burst Reporters:[/bold]")
                for i, reporter in enumerate(reporters_data, 1):
                    console.print(f"[bold]Reporter {i}:[/bold]")
                    for key, value in reporter.items():
                        console.print(f"  [dim]{key}:[/dim] {value}")
                    console.print()  # Empty line between reporters

            except EeroAPIException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    console.print(
                        "[bold yellow]Burst reporters feature is not available for this network[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may require a premium Eero subscription or may not be enabled in your network settings.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error getting burst reporters: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(get_burst_reporters)

    asyncio.run(run_command())
