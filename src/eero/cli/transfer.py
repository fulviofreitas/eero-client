"""Transfer commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
from .formatting import console
from .utils import run_with_client


@click.command(hidden=True)
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@click.option("--device-id", help="Device ID to get transfer stats for (optional)")
def transfer(network_id: Optional[str], device_id: Optional[str]) -> None:
    """Get transfer statistics."""

    async def run_command() -> None:
        async def get_transfer_stats(client: EeroClient) -> None:
            try:
                with console.status("Getting transfer statistics..."):
                    transfer_data = await client.get_transfer_stats(network_id, device_id)

                if not transfer_data:
                    console.print("[bold yellow]No transfer data found[/bold yellow]")
                    return

                # Print transfer data in a formatted way
                console.print("[bold]Transfer Statistics:[/bold]")
                for key, value in transfer_data.items():
                    if isinstance(value, dict):
                        console.print(f"[bold]{key}:[/bold]")
                        for sub_key, sub_value in value.items():
                            console.print(f"  [dim]{sub_key}:[/dim] {sub_value}")
                    else:
                        console.print(f"[bold]{key}:[/bold] {value}")

            except EeroAPIException as e:
                if "403" in str(e) or "access.denied" in str(e).lower():
                    console.print(
                        "[bold yellow]Transfer feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                elif "404" in str(e) or "not found" in str(e).lower():
                    console.print(
                        "[bold yellow]Transfer feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error getting transfer statistics: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(get_transfer_stats)

    asyncio.run(run_command())
