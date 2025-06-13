"""Utility functions for the Eero CLI."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from rich.console import Console
from rich.prompt import Confirm

from ..client import EeroClient
from ..exceptions import EeroException

# Create console for rich output
console = Console()


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


def load_config() -> Dict[str, Any]:
    """Load configuration from file.

    Returns:
        Configuration dictionary
    """
    config_file = get_config_file()
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    config_file = get_config_file()
    with open(config_file, "w") as f:
        json.dump(config, f)


def get_preferred_network() -> Optional[str]:
    """Get the preferred network ID from configuration.

    Returns:
        Preferred network ID or None if not set
    """
    config = load_config()
    return config.get("preferred_network_id")


def set_preferred_network(network_id: str) -> None:
    """Set the preferred network ID in configuration.

    Args:
        network_id: Network ID to set as preferred
    """
    config = load_config()
    config["preferred_network_id"] = network_id
    save_config(config)


async def run_with_client(func: Callable[[EeroClient], Any]) -> Any:
    """Run a function with an authenticated EeroClient.

    Args:
        func: Async function to run with client

    Returns:
        Result of the function call
    """
    from .auth import interactive_login

    async with EeroClient(cookie_file=str(get_cookie_file())) as client:
        if not client.is_authenticated:
            console.print("[bold yellow]Not authenticated. Please login.[/bold yellow]")
            if not await interactive_login(client):
                return None

        # Get preferred network from config if not already set
        if not client._api.preferred_network_id:
            preferred_network_id = get_preferred_network()
            if preferred_network_id:
                client.set_preferred_network(preferred_network_id)

        return await func(client)


def confirm_action(message: str) -> bool:
    """Prompt for confirmation before performing an action.

    Args:
        message: Message to display in the confirmation prompt

    Returns:
        True if confirmed, False otherwise
    """
    return Confirm.ask(message)
