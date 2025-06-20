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
def cli(ctx, debug: bool, no_keyring: bool):
    """Eero network management command-line tool."""
    # Set up the console
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Store configuration in context for subcommands
    ctx.obj = {"no_keyring": no_keyring}


from .ac_compat import ac_compat

# Import and add commands
from .auth import clear_auth, login, logout, resend_code
from .blacklist import blacklist
from .burst_reporters import burst_reporters
from .devices import block_device, device, devices, rename_device

# Import new commands
from .diagnostics import diagnostics
from .eeros import eero, eeros, reboot
from .forwards import forwards
from .guest import guest_network
from .insights import insights
from .networks import network, networks, set_network
from .ouicheck import ouicheck
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

# Register all commands
cli.add_command(login, name="login")
cli.add_command(logout, name="logout")
cli.add_command(resend_code, name="resend-code")
cli.add_command(clear_auth, name="clear-auth")

cli.add_command(networks, name="networks")
cli.add_command(network, name="network")
cli.add_command(set_network, name="set-network")

cli.add_command(eeros, name="eeros")
cli.add_command(eero, name="eero")
cli.add_command(reboot, name="reboot")

cli.add_command(devices, name="devices")
cli.add_command(device, name="device")
cli.add_command(rename_device, name="rename-device")
cli.add_command(block_device, name="block-device")

cli.add_command(profiles, name="profiles")
cli.add_command(profile, name="profile")
cli.add_command(pause_profile, name="pause-profile")

cli.add_command(guest_network, name="guest-network")
cli.add_command(speedtest, name="speedtest")

# Register new commands
cli.add_command(diagnostics, name="diagnostics")
cli.add_command(settings, name="settings")
cli.add_command(insights, name="insights")
cli.add_command(routing, name="routing")
cli.add_command(thread, name="thread")
cli.add_command(support, name="support")
cli.add_command(blacklist, name="blacklist")
cli.add_command(reservations, name="reservations")
cli.add_command(forwards, name="forwards")
cli.add_command(transfer, name="transfer")
cli.add_command(burst_reporters, name="burst-reporters")
cli.add_command(ac_compat, name="ac-compat")
cli.add_command(ouicheck, name="ouicheck")
cli.add_command(password, name="password")
cli.add_command(updates, name="updates")


def main():
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


def run():
    """Run function called by entry point."""
    main()


if __name__ == "__main__":
    main()
