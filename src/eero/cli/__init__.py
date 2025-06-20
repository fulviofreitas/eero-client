"""Command-line interface for Eero client."""

import logging
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

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
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug: bool):
    """Eero network management command-line tool."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)


# Import and add commands
from .auth import clear_auth, login, logout, resend_code
from .devices import block_device, device, devices, rename_device
from .eeros import eero, eeros, reboot
from .guest import guest_network
from .networks import network, networks, set_network
from .profiles import pause_profile, profile, profiles
from .speedtest import speedtest

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


def main():
    """Main entry point for the CLI."""
    try:
        # Remove version information print
        # from .. import __version__
        # console.print(f"Eero Client v{__version__}")
        cli()
    except Exception as ex:
        console.print(f"[bold red]Error:[/bold red] {ex}")
        if logging.getLogger().level == logging.DEBUG:
            console.print_exception()
        sys.exit(1)


def run():
    """Run function called by entry point."""
    main()


if __name__ == "__main__":
    main()
