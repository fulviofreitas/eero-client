"""Support commands for the Eero CLI."""

import asyncio
from typing import Optional

import click
from rich.table import Table

from ..client import EeroClient
from ..exceptions import EeroAPIException, EeroException
from .formatting import console
from .utils import run_with_client


def format_support_info(support_data: dict) -> None:
    """Format and display support information in a user-friendly way."""

    # Create a summary table
    table = Table(
        title="[bold blue]Eero Support Information[/bold blue]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Contact Method", style="cyan", no_wrap=True)
    table.add_column("Details", style="white")

    # Add support information to the table
    if "support_phone" in support_data:
        table.add_row("📞 Phone", support_data["support_phone"])

    if "email_web_form_url" in support_data:
        email_url = support_data["email_web_form_url"]
        if email_url.startswith("mailto:"):
            email = email_url.replace("mailto:", "")
            table.add_row("📧 Email", email)
        else:
            table.add_row("📧 Email", email_url)

    if "help_url" in support_data:
        table.add_row("🌐 Help Center", support_data["help_url"])

    if "contact_url" in support_data:
        table.add_row("📋 Contact Form", support_data["contact_url"])

    if "name" in support_data:
        table.add_row("🏢 Company", support_data["name"].title())

    # Display the table
    console.print(table)

    # Show additional information if available
    additional_info = []
    for key, value in support_data.items():
        if key not in ["support_phone", "email_web_form_url", "help_url", "contact_url", "name"]:
            additional_info.append((key, value))

    if additional_info:
        console.print("\n[bold yellow]Additional Information:[/bold yellow]")
        for key, value in additional_info:
            console.print(f"  [dim]{key.replace('_', ' ').title()}:[/dim] {value}")


@click.command()
@click.option("--network-id", help="Network ID (uses preferred network if not specified)")
def support(network_id: Optional[str]) -> None:
    """Get network support information."""

    async def run_command() -> None:
        async def get_support(client: EeroClient) -> None:
            try:
                with console.status("Getting network support information..."):
                    support_data = await client.get_support(network_id)

                if not support_data:
                    console.print("[bold yellow]No support data found[/bold yellow]")
                    return

                format_support_info(support_data)

            except EeroAPIException as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    console.print(
                        "[bold yellow]Support feature is not implemented by this API/CLI[/bold yellow]"
                    )
                    console.print(
                        "[dim]This feature may not be available in the current version of the Eero API.[/dim]"
                    )
                else:
                    console.print(f"[bold red]Error getting support information: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Unexpected error: {e}[/bold red]")

        await run_with_client(get_support)

    asyncio.run(run_command())
