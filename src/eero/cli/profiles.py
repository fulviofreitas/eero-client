"""Profile commands for the Eero CLI."""

import asyncio
import json
from typing import Optional

import click
from pydantic import ValidationError
from rich.panel import Panel

from ..client import EeroClient
from ..exceptions import EeroException
from ..models.profile import Profile
from .formatting import (
    console,
    create_profiles_table,
    print_profile_details,
    print_profile_details_brief,
)
from .utils import get_cookie_file, output_option, run_with_client


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def profiles(ctx: click.Context, network_id: Optional[str], output: str) -> None:
    """List all profiles in a network."""

    async def run_command() -> None:
        async def get_profiles(client: EeroClient) -> None:
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

            with console.status("Getting profiles..."):
                try:
                    profiles = await client.get_profiles(network_id)
                except ValidationError as ve:
                    console.print("[bold red]Profile data validation error![/bold red]")
                    console.print(str(ve))
                    # Optionally, print the raw data for debugging
                    try:
                        # get_profiles in API expects str, so fallback to preferred_network_id if needed
                        net_id = network_id or client._api.preferred_network_id
                        if not net_id:
                            raise EeroException("No network ID available for raw API fetch.")
                        raw_profiles = await client._api.profiles.get_profiles(net_id)
                        console.print("[bold yellow]Raw API response:[/bold yellow]")
                        console.print(raw_profiles)
                    except Exception as api_ex:
                        console.print(
                            f"[bold red]Failed to fetch raw API response: {api_ex}[/bold red]"
                        )
                    return
                except Exception as ex:
                    console.print(f"[bold red]Error fetching profiles: {ex}[/bold red]")
                    return

            if not profiles:
                console.print("[bold yellow]No profiles found[/bold yellow]")
                return

            if output_format == "json":
                if len(profiles) == 1:
                    console.print(profiles[0].model_dump_json(indent=4))
                else:
                    # Create a properly formatted JSON array
                    # Convert each profile to dict with JSON mode to handle datetime objects
                    profiles_data = [p.model_dump(mode="json") for p in profiles]
                    console.print(json.dumps(profiles_data, indent=4))
            else:
                table = create_profiles_table(profiles)
                console.print(table)

        await run_with_client(get_profiles)

    asyncio.run(run_command())


@click.command()
@click.argument("profile_identifier")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
@output_option
@click.pass_context
def profile(
    ctx: click.Context, profile_identifier: str, network_id: Optional[str], output: str
) -> None:
    """Show profile details."""

    async def run_command() -> None:
        async def get_profile_details(client: EeroClient) -> None:
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

            nonlocal network_id
            if not network_id:
                try:
                    network = await client.get_network()
                    network_id = network.id
                except EeroException as e:
                    console.print(f"[bold red]Error: {e}[/bold red]")
                    return

            with console.status("Getting profiles..."):
                profiles = await client.get_profiles(network_id)

            target_profile = None
            for p in profiles:
                if p.id == profile_identifier or p.name == profile_identifier:
                    target_profile = p
                    break

            if not target_profile or not target_profile.id:
                console.print(f"[bold red]Profile '{profile_identifier}' not found[/bold red]")
                return

            with console.status("Getting profile details..."):
                profile_details = await client.get_profile(target_profile.id, network_id)

            if output_format == "brief":
                print_profile_details_brief(profile_details)
            elif output_format == "extensive":
                print_profile_details_extensive(profile_details)
            elif output_format == "json":
                # Using .model_dump_json() for serialization
                console.print(profile_details.model_dump_json(indent=4))

        await run_with_client(get_profile_details)

    asyncio.run(run_command())


@click.command()
@click.argument("profile-id")
@click.option("--pause/--unpause", required=True, help="Pause or unpause the profile")
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def pause_profile(profile_id: str, pause: bool, network_id: Optional[str]) -> None:
    """Pause or unpause internet access for a profile."""

    async def run_command() -> None:
        async def toggle_pause(client: EeroClient) -> None:
            action = "Pausing" if pause else "Unpausing"
            with console.status(f"{action} profile..."):
                result = await client.pause_profile(
                    profile_id=profile_id, paused=pause, network_id=network_id
                )

            if result:
                status = "paused" if pause else "unpaused"
                console.print(f"[bold green]Profile {status} successfully[/bold green]")
            else:
                console.print("[bold red]Failed to update profile pause status[/bold red]")

        await run_with_client(toggle_pause)

    asyncio.run(run_command())


def print_profile_details_extensive(profile: Profile) -> None:
    """Print extensive profile information including all available fields.

    Args:
        profile: Profile object
    """
    paused_style = "red" if profile.paused else "green"

    # Basic Profile Information
    basic_panel = Panel(
        f"[bold]ID:[/bold] {profile.id}\n"
        f"[bold]Name:[/bold] {profile.name}\n"
        f"[bold]Network ID:[/bold] {profile.network_id}\n"
        f"[bold]Device Count:[/bold] {profile.device_count}\n"
        f"[bold]Connected Device Count:[/bold] {profile.connected_device_count}\n"
        f"[bold]Paused:[/bold] [{paused_style}]{'Yes' if profile.paused else 'No'}[/{paused_style}]\n"
        f"[bold]Premium Enabled:[/bold] {'Yes' if profile.premium_enabled else 'No'}\n"
        f"[bold]Schedule Enabled:[/bold] {'Yes' if profile.schedule_enabled else 'No'}",
        title=f"Profile: {profile.name}",
        border_style="blue",
    )
    console.print(basic_panel)

    # Device IDs
    if profile.device_ids:
        device_panel = Panel(
            "\n".join(profile.device_ids),
            title="Device IDs",
            border_style="cyan",
        )
        console.print(device_panel)

    # Schedule
    if profile.schedule_enabled and profile.schedule_blocks:
        schedule_panel = Panel(
            "\n".join(
                f"[bold]{', '.join(block.days)}:[/bold] {block.start_time} - {block.end_time}"
                for block in profile.schedule_blocks
            ),
            title="Schedule Blocks",
            border_style="green",
        )
        console.print(schedule_panel)

    # Content filter
    if profile.content_filter:
        content_filter = profile.content_filter
        filter_enabled = any(vars(content_filter).values())

        if filter_enabled:
            filter_settings = []
            for name, value in vars(content_filter).items():
                if value:
                    # Convert snake_case to title case for display
                    display_name = " ".join(word.capitalize() for word in name.split("_"))
                    filter_settings.append(f"[bold]{display_name}:[/bold] Enabled")

            filter_panel = Panel(
                "\n".join(filter_settings),
                title="Content Filtering",
                border_style="yellow",
            )
            console.print(filter_panel)

    # Block/Allow lists
    if profile.custom_block_list:
        block_panel = Panel(
            "\n".join(profile.custom_block_list),
            title="Blocked Domains",
            border_style="red",
        )
        console.print(block_panel)

    if profile.custom_allow_list:
        allow_panel = Panel(
            "\n".join(profile.custom_allow_list),
            title="Allowed Domains",
            border_style="green",
        )
        console.print(allow_panel)

    # Usage statistics
    if profile.usage:
        usage_panel = Panel(
            str(profile.usage),
            title="Usage Statistics",
            border_style="magenta",
        )
        console.print(usage_panel)
