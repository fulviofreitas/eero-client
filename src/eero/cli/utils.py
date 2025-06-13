"""Utility functions for the Eero CLI."""

import asyncio
import json
import os
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, cast

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ..client import EeroClient
from ..exceptions import EeroException
from .auth import interactive_login

# Type for async functions that accept an EeroClient
F = TypeVar("F", bound=Callable[..., Any])


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


def with_eero_client(func: F) -> F:
    """Decorator to run a function with an authenticated EeroClient.

    Args:
        func: Async function to decorate that accepts an EeroClient as first arg

    Returns:
        Decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        ctx = typer.Context.get_current()
        console = ctx.obj.get("console", Console())
        cookie_file = ctx.obj.get("cookie_file")
        use_keyring = ctx.obj.get("use_keyring", True)

        async def run_with_client():
            async with EeroClient(
                cookie_file=cookie_file, use_keyring=use_keyring
            ) as client:
                if not client.is_authenticated:
                    console.print(
                        "[bold yellow]Not authenticated. Please login.[/bold yellow]"
                    )
                    if not await interactive_login(client):
                        return None

                # Get preferred network from config if not already set
                if not client._api.preferred_network_id:
                    preferred_network_id = get_preferred_network()
                    if preferred_network_id:
                        client.set_preferred_network(preferred_network_id)

                return await func(client, *args, **kwargs)

        return asyncio.run(run_with_client())

    return cast(F, wrapper)


def confirm_action(message: str) -> bool:
    """Prompt for confirmation before performing an action.

    Args:
        message: Message to display in the confirmation prompt

    Returns:
        True if confirmed, False otherwise
    """
    return Confirm.ask(message)
