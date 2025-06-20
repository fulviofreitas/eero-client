"""Authentication commands for the Eero CLI."""

import asyncio
import json
import os
import sys
from typing import Optional

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ..client import EeroClient
from ..exceptions import EeroException
from .utils import console, get_cookie_file


async def interactive_login(client: EeroClient, force: bool = False) -> bool:
    """Interactive login process.

    Args:
        client: EeroClient instance
        force: Whether to force a new login

    Returns:
        True if login was successful
    """
    attempts = 0
    max_attempts = 3
    user_identifier = None
    cookie_file = get_cookie_file()

    # Check if cookie file exists
    if os.path.exists(cookie_file) and not force:
        try:
            with open(cookie_file, "r") as f:
                cookies = json.load(f)
                user_token = cookies.get("user_token")
                session_id = cookies.get("session_id")
                session_expiry = cookies.get("session_expiry")

                if user_token and session_id:
                    console.print(
                        Panel.fit(
                            "An existing authentication session was found.",
                            title="Eero Login",
                            border_style="blue",
                        )
                    )
                    reuse = Confirm.ask("Do you want to reuse the existing session?")

                    if reuse:
                        console.print(
                            "[bold yellow]Reusing existing session[/bold yellow]"
                        )
                        # Try to use the existing session
                        try:
                            with console.status("Testing existing session..."):
                                # Get networks to test the session
                                networks = await client.get_networks()
                                console.print(
                                    f"[bold green]Session valid! Found {len(networks)} networks.[/bold green]"
                                )
                                return True
                        except EeroException as ex:
                            console.print(
                                f"[bold red]Existing session invalid: {ex}[/bold red]"
                            )
                            console.print(
                                "[bold yellow]Starting new authentication process...[/bold yellow]"
                            )
                            # Continue with new auth process
                        except Exception as ex:
                            console.print(
                                f"[bold red]Error testing session: {ex}[/bold red]"
                            )
                            console.print(
                                "[bold yellow]Starting new authentication process...[/bold yellow]"
                            )
                            # Continue with new auth process
                    else:
                        console.print(
                            "[bold yellow]Starting new authentication process...[/bold yellow]"
                        )
        except Exception as e:
            console.print(f"[bold red]Error reading cookie file: {e}[/bold red]")

    # Force clear existing auth data if we get here
    await client._api.auth.clear_auth_data()
    console.print("[bold yellow]Cleared existing authentication data[/bold yellow]")

    while attempts < max_attempts:
        # Only ask for identifier on first attempt
        if attempts == 0:
            console.print(
                Panel.fit(
                    "Please login to your Eero account. A verification code will be sent to you.",
                    title="Eero Login",
                    border_style="blue",
                )
            )
            user_identifier = Prompt.ask("Email or phone number")

            with console.status("Requesting verification code..."):
                try:
                    result = await client.login(user_identifier)
                    if not result:
                        console.print(
                            "[bold red]Failed to request verification code[/bold red]"
                        )
                        return False
                    console.print("[bold green]Verification code sent![/bold green]")
                except EeroException as ex:
                    console.print(f"[bold red]Error:[/bold red] {ex}")
                    return False

        verification_code = Prompt.ask("Verification code (check your email/phone)")

        with console.status("Verifying..."):
            try:
                result = await client.verify(verification_code)
                if result:
                    console.print("[bold green]Login successful![/bold green]")
                    return True
                else:
                    console.print("[bold red]Verification failed[/bold red]")
            except EeroException as ex:
                console.print(f"[bold red]Error:[/bold red] {ex}")

        # If we get here, verification failed
        attempts += 1
        if attempts < max_attempts:
            resend = Confirm.ask("Would you like to resend the verification code?")
            if resend:
                with console.status("Resending verification code..."):
                    try:
                        result = await client._api.auth.resend_verification_code()
                        if result:
                            console.print(
                                "[bold green]Verification code resent![/bold green]"
                            )
                        else:
                            console.print(
                                "[bold red]Failed to resend verification code[/bold red]"
                            )
                    except EeroException as ex:
                        console.print(f"[bold red]Error:[/bold red] {ex}")
                        return False
            else:
                # User doesn't want to resend, exit the loop
                break

    if attempts >= max_attempts:
        console.print("[bold red]Too many failed verification attempts[/bold red]")
        return False

    return False


@click.command()
@click.option(
    "--force", is_flag=True, help="Force new login even if already authenticated"
)
def login(force: bool):
    """Login to your Eero account."""

    async def run():
        async with EeroClient(cookie_file=str(get_cookie_file())) as client:
            if client.is_authenticated and not force:
                console.print(
                    "[bold yellow]Already authenticated. Use --force to login again.[/bold yellow]"
                )
                return

            await interactive_login(client, force)

    asyncio.run(run())


@click.command()
def logout():
    """Logout from your Eero account."""

    async def run():
        async with EeroClient(cookie_file=str(get_cookie_file())) as client:
            if not client.is_authenticated:
                console.print("[bold red]Not logged in[/bold red]")
                return

            with console.status("Logging out..."):
                try:
                    result = await client.logout()

                    if result:
                        console.print(
                            "[bold green]Logged out successfully[/bold green]"
                        )
                    else:
                        console.print("[bold red]Failed to logout[/bold red]")
                except EeroException as ex:
                    console.print(f"[bold red]Error:[/bold red] {ex}")

    asyncio.run(run())


@click.command()
def resend_code():
    """Resend verification code during login process."""

    async def run():
        async with EeroClient(cookie_file=str(get_cookie_file())) as client:
            # Check if we have a user token but not authenticated yet
            if client._api.auth._user_token and not client.is_authenticated:
                with console.status("Resending verification code..."):
                    try:
                        result = await client._api.auth.resend_verification_code()
                        if result:
                            console.print(
                                "[bold green]Verification code resent successfully![/bold green]"
                            )

                            # Now try to verify
                            verification_code = Prompt.ask("Enter verification code")
                            with console.status("Verifying..."):
                                try:
                                    result = await client.verify(verification_code)
                                    if result:
                                        console.print(
                                            "[bold green]Login successful![/bold green]"
                                        )
                                    else:
                                        console.print(
                                            "[bold red]Verification failed[/bold red]"
                                        )
                                except EeroException as ex:
                                    console.print(f"[bold red]Error:[/bold red] {ex}")
                        else:
                            console.print(
                                "[bold red]Failed to resend verification code[/bold red]"
                            )
                    except EeroException as ex:
                        console.print(f"[bold red]Error:[/bold red] {ex}")
            else:
                console.print(
                    "[bold yellow]No active login attempt found.[/bold yellow]"
                )
                console.print(
                    "[bold yellow]Please start a new login process with 'eero login'[/bold yellow]"
                )

    asyncio.run(run())


@click.command()
def clear_auth():
    """Clear all authentication data."""

    async def run():
        async with EeroClient(cookie_file=str(get_cookie_file())) as client:
            await client._api.auth.clear_auth_data()
            console.print(
                "[bold green]Authentication data cleared successfully[/bold green]"
            )

    asyncio.run(run())
