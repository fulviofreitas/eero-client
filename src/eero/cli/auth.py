"""Authentication commands for the Eero CLI."""

import asyncio
import sys
from typing import Optional

import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ..client import EeroClient
from ..exceptions import EeroException

login_commands = typer.Typer(help="Authentication commands")


async def interactive_login(client: EeroClient) -> bool:
    """Interactive login process.

    Args:
        client: EeroClient instance

    Returns:
        True if login was successful
    """
    console = typer.get_app().state.console
    attempts = 0
    max_attempts = 3
    user_identifier = None

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


@login_commands.command(name="login")
def login_command():
    """Login to your Eero account."""
    ctx = typer.Context.get_current()
    console = ctx.obj["console"]
    cookie_file = ctx.obj["cookie_file"]
    use_keyring = ctx.obj["use_keyring"]

    async def run():
        async with EeroClient(
            cookie_file=cookie_file, use_keyring=use_keyring
        ) as client:
            await interactive_login(client)

    asyncio.run(run())


@login_commands.command(name="logout")
def logout_command():
    """Logout from your Eero account."""
    ctx = typer.Context.get_current()
    console = ctx.obj["console"]
    cookie_file = ctx.obj["cookie_file"]
    use_keyring = ctx.obj["use_keyring"]

    async def run():
        async with EeroClient(
            cookie_file=cookie_file, use_keyring=use_keyring
        ) as client:
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


@login_commands.command(name="resend-code")
def resend_code_command():
    """Resend verification code during login process."""
    ctx = typer.Context.get_current()
    console = ctx.obj["console"]
    cookie_file = ctx.obj["cookie_file"]
    use_keyring = ctx.obj["use_keyring"]

    async def run():
        async with EeroClient(
            cookie_file=cookie_file, use_keyring=use_keyring
        ) as client:
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
                    "[bold yellow]Please start a new login process with 'eero auth login'[/bold yellow]"
                )

    asyncio.run(run())
