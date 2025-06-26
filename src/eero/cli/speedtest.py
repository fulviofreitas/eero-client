"""Speed test commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
from .formatting import console, print_speedtest_results
from .utils import get_cookie_file, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def speedtest(network_id: Optional[str]) -> None:
    """Run a speed test on your network."""

    async def run_command() -> None:
        async def run_speedtest(client: EeroClient) -> None:
            try:
                with console.status("Running speed test (this may take a minute)..."):
                    result = await client.run_speed_test(network_id)

                console.print("[bold green]Speed test completed:[/bold green]")
                print_speedtest_results(result)
            except EeroAPIException as e:
                if "202" in str(e):
                    console.print(
                        "[bold yellow]Speed test is in progress or not yet available. Please try again in a moment.[/bold yellow]"
                    )
                else:
                    console.print(f"[bold red]Error running speed test: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(run_speedtest)

    asyncio.run(run_command())
