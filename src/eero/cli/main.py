"""Command-line interface for Eero client."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from .. import __version__
from ..client import EeroClient
from ..exceptions import EeroException
from .utils import output_option

# Create console for rich output
console = Console()

# Set up logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)


@click.group()
@click.version_option(
    version=f"{__version__} (Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})",
    prog_name="Eero Client",
)
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--no-keyring",
    is_flag=True,
    help="Don't use keyring for secure token storage",
    default=False,
)
@click.pass_context
def cli(ctx: click.Context, debug: bool, no_keyring: bool) -> None:
    """Eero network management command-line tool."""
    # Set up the console
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Store configuration in context for subcommands
    ctx.obj = {"no_keyring": no_keyring}


# Import all command modules
from .ac_compat import ac_compat
from .auth import clear_auth, login, logout, resend_code
from .blacklist import blacklist
from .devices import block_device, device, devices, rename_device
from .diagnostics import diagnostics
from .eeros import eero, eeros, reboot_standalone
from .forwards import forwards
from .guest import guest_network
from .insights import insights
from .networks import network, networks, set_network
from .password import password
from .profiles import pause_profile, profile, profiles
from .reservations import reservations
from .routing import routing
from .settings import settings
from .speedtest import speedtest
from .support import support
from .thread import thread
from .transfer import transfer
from .updates import updates


# Create network subcommand group
@cli.group()
def network_group() -> None:
    """Network management commands."""
    pass


# Create devices subcommand group
@cli.group()
def devices_group() -> None:
    """Device management commands."""
    pass


# Create device subcommand group
@cli.group()
def device_group() -> None:
    """Individual device management commands."""
    pass


# Create profile subcommand group
@cli.group()
def profile_group() -> None:
    """Profile management commands."""
    pass


# Create login subcommand group
@cli.group()
def login_group() -> None:
    """Login management commands."""
    pass


# Create logout subcommand group
@cli.group()
def logout_group() -> None:
    """Logout management commands."""
    pass


# Create eeros subcommand group
@cli.group()
def eeros_group() -> None:
    """Eero device management commands."""
    pass


# Register authentication commands
cli.add_command(login, name="login")
cli.add_command(logout, name="logout")
cli.add_command(resend_code, name="resend-code")
cli.add_command(clear_auth, name="clear-auth")

# Register network commands
cli.add_command(networks, name="networks")
cli.add_command(network, name="network")
cli.add_command(set_network, name="set-network")

# Register eeros commands
cli.add_command(eeros, name="eeros")
cli.add_command(eero, name="eero")
cli.add_command(reboot_standalone, name="reboot")

# Register device commands
cli.add_command(devices, name="devices")
cli.add_command(device, name="device")

# Register profile commands
cli.add_command(profiles, name="profiles")
cli.add_command(profile, name="profile")

# Register guest network command
cli.add_command(guest_network, name="guest-network")

# Register subcommand groups
cli.add_command(network_group, name="network")
cli.add_command(devices_group, name="devices")
cli.add_command(device_group, name="device")
cli.add_command(profile_group, name="profile")
cli.add_command(eeros_group, name="eeros")

# Add subcommands to network group
network_group.add_command(ac_compat, name="ac-compat")
network_group.add_command(diagnostics, name="diagnostics")
network_group.add_command(forwards, name="forwards")
network_group.add_command(reservations, name="reservations")
network_group.add_command(settings, name="settings")
network_group.add_command(speedtest, name="speedtest")
network_group.add_command(transfer, name="transfer")
network_group.add_command(updates, name="updates")
network_group.add_command(support, name="support")
network_group.add_command(insights, name="insights")
network_group.add_command(routing, name="routing")
network_group.add_command(thread, name="thread")

# Add subcommands to devices group
devices_group.add_command(blacklist, name="blacklist")

# Add subcommands to device group
device_group.add_command(rename_device, name="rename")
device_group.add_command(block_device, name="block")

# Add subcommands to profile group
profile_group.add_command(pause_profile, name="pause")

# Add subcommands to eeros group
eeros_group.add_command(updates, name="updates")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except EeroException as ex:
        console.print(f"[bold red]Error:[/bold red] {ex}")
        sys.exit(1)
    except Exception as ex:
        console.print(f"[bold red]Unexpected error:[/bold red] {ex}")
        if logging.getLogger().level == logging.DEBUG:
            console.print_exception()
        sys.exit(1)


def run() -> None:
    """Run function called by entry point."""
    main()


if __name__ == "__main__":
    main()
