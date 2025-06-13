"""Profile commands for the Eero CLI."""

import asyncio
from typing import Optional

import click

from ..client import EeroClient
from ..exceptions import EeroException
from .formatting import console, create_profiles_table, print_profile_details
from .utils import get_cookie_file, run_with_client


@click.command()
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def profiles(network_id: Optional[str]):
    """List all profiles in a network."""

    async def run_command():
        async def get_profiles(client: EeroClient):
            with console.status("Getting profiles..."):
                profiles = await client.get_profiles(network_id)

            if not profiles:
                console.print("[bold yellow]No profiles found[/bold yellow]")
                return

            table = create_profiles_table(profiles)
            console.print(table)

        await run_with_client(get_profiles)

    asyncio.run(run_command())


@click.command()
@click.argument("profile-id")
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def profile(profile_id: str, network_id: Optional[str]):
    """Show profile details."""

    async def run_command():
        async def get_profile_details(client: EeroClient):
            with console.status("Getting profile details..."):
                profile = await client.get_profile(profile_id, network_id)

            print_profile_details(profile)

        await run_with_client(get_profile_details)

    asyncio.run(run_command())


@click.command()
@click.argument("profile-id")
@click.option("--pause/--unpause", required=True, help="Pause or unpause the profile")
@click.option(
    "--network-id", help="Network ID (uses preferred network if not specified)"
)
def pause_profile(profile_id: str, pause: bool, network_id: Optional[str]):
    """Pause or unpause internet access for a profile."""

    async def run_command():
        async def toggle_pause(client: EeroClient):
            action = "Pausing" if pause else "Unpausing"
            with console.status(f"{action} profile..."):
                result = await client.pause_profile(
                    profile_id=profile_id, paused=pause, network_id=network_id
                )

            if result:
                status = "paused" if pause else "unpaused"
                console.print(f"[bold green]Profile {status} successfully[/bold green]")
            else:
                console.print(
                    "[bold red]Failed to update profile pause status[/bold red]"
                )

        await run_with_client(toggle_pause)

    asyncio.run(run_command())
