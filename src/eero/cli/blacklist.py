"""Blacklist commands for the Eero CLI."""

import asyncio
import json
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console, create_blacklist_table
from .utils import output_option, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def blacklist(ctx: click.Context, network_id: Optional[str], output: str) -> None:
    """Get device blacklist."""

    async def run_command() -> None:
        async def get_blacklist(client: EeroClient) -> None:
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

            with console.status("Getting device blacklist..."):
                blacklist_data = await client.get_blacklist(network_id)

            if not blacklist_data:
                console.print("[bold yellow]No blacklisted devices found[/bold yellow]")
                return

            if output_format == "json":
                if len(blacklist_data) == 1:
                    console.print(json.dumps(blacklist_data[0], indent=4))
                else:
                    console.print(json.dumps(blacklist_data, indent=4))
            else:
                table = create_blacklist_table(blacklist_data)
                console.print(table)

        await run_with_client(get_blacklist)

    asyncio.run(run_command())
