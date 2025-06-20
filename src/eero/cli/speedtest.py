"""Speed test commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console, print_speedtest_results
from .utils import get_cookie_file, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def speedtest(network_id: Optional[str]):
    """Run a speed test on your network."""

    async def run_command():
        async def run_speedtest(client: EeroClient):
            with console.status("Running speed test (this may take a minute)..."):
                result = await client.run_speed_test(network_id)

            console.print("[bold green]Speed test completed:[/bold green]")
            print_speedtest_results(result)

        await run_with_client(run_speedtest)

    asyncio.run(run_command())
