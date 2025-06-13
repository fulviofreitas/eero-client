"""Command-line interface for Eero client."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console
from rich.logging import RichHandler

from ..client import EeroClient
from ..exceptions import EeroException
from .auth import login_commands, logout_command, resend_code_command
from .devices import devices_commands
from .eeros import eeros_commands
from .guest import guest_network_commands
from .networks import networks_commands
from .profiles import profiles_commands
from .speedtest import speedtest_command

# Create console for rich output
console = Console()

# Set up logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)

# Create Typer app
app = typer.Typer(
    name="eero",
    help="Eero network management command-line tool",
    add_completion=True,
    rich_markup_mode="rich",
)

# Add subcommands
app.add_typer(login_commands, name="auth", help="Authentication commands")
app.add_typer(networks_commands, name="networks", help="Network management commands")
app.add_typer(eeros_commands, name="eeros", help="Eero device commands")
app.add_typer(devices_commands, name="devices", help="Device management commands")
app.add_typer(profiles_commands, name="profiles", help="Profile management commands")

# Add standalone commands
app.command(name="speedtest")(speedtest_command)
app.command(name="guest-network")(guest_network_commands)


def get_config_dir() -> Path:
    """Get the configuration directory.

    Returns:
        Path to the configuration directory
    """
    if sys.platform == "win32":
        config_dir = Path(os.environ["APPDATA"]) / "eero-client"
    else:
        config_dir = Path.home() / ".config" / "eero-client"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cookie_file() -> Path:
    """Get the cookie file path.

    Returns:
        Path to the cookie file
    """
    return get_config_dir() / "cookies.json"


def get_config_file() -> Path:
    """Get the config file path.

    Returns:
        Path to the config file
    """
    return get_config_dir() / "config.json"


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    use_keyring: bool = typer.Option(
        True,
        "--no-keyring",
        help="Don't use keyring for secure token storage",
        show_default=False,
    ),
):
    """Eero network management command-line tool."""
    # Set up the console
    ctx.ensure_object(dict)
    ctx.obj["console"] = console

    # Update logging level if debug mode is enabled
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")

    # Store configuration options in context
    ctx.obj["use_keyring"] = use_keyring
    ctx.obj["cookie_file"] = str(get_cookie_file()) if not use_keyring else None

    # Display version information
    from .. import __version__

    console.print(f"Eero Client v{__version__}")


def run():
    """Run the CLI application."""
    try:
        app()
    except EeroException as ex:
        console.print(f"[bold red]Error:[/bold red] {ex}")
        sys.exit(1)
    except Exception as ex:
        console.print(f"[bold red]Unexpected error:[/bold red] {ex}")
        if logging.getLogger().level == logging.DEBUG:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    run()
