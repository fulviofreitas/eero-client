"""Utility functions for the Eero CLI."""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import click
import keyring
from rich.console import Console

from ..client import EeroClient
from ..exceptions import EeroException

# Create console for rich output
console = Console()


def output_option(func):
    """Decorator to add --output option to commands."""
    return click.option(
        "--output",
        type=click.Choice(["brief", "extensive", "json"]),
        default="brief",
        help="Output format (brief, extensive, or json)",
    )(func)


def get_config_dir() -> Path:
    """Get the configuration directory.

    Returns:
        Path to the configuration directory
    """
    if os.name == "nt":  # Windows
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


def set_preferred_network(network_id: str) -> None:
    """Set the preferred network ID in the configuration.

    Args:
        network_id: The network ID to set as preferred
    """
    config_file = get_config_file()
    config = {}

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    config["preferred_network_id"] = network_id

    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        console.print(f"[bold red]Error saving config: {e}[/bold red]")


def get_preferred_network() -> Optional[str]:
    """Get the preferred network ID from the configuration.

    Returns:
        The preferred network ID or None if not set
    """
    config_file = get_config_file()

    if not config_file.exists():
        return None

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config.get("preferred_network_id")
    except (json.JSONDecodeError, IOError):
        return None


async def run_with_client(func):
    """Run a function with an EeroClient instance.

    Args:
        func: Async function that takes an EeroClient as argument
    """
    cookie_file = get_cookie_file()

    async with EeroClient(cookie_file=str(cookie_file)) as client:
        await func(client)


def confirm_action(message: str) -> bool:
    """Ask user to confirm an action.

    Args:
        message: The message to display

    Returns:
        True if user confirms, False otherwise
    """
    return click.confirm(message)
