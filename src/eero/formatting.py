"""
This contains the update to the create_network_table function in formatting.py.
You should add this function to the existing formatting.py file.
"""


def create_network_table(networks: List[Network]) -> Table:
    """Create a table displaying networks.

    Args:
        networks: List of Network objects

    Returns:
        Rich Table object
    """
    table = Table(title="Eero Networks")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Public IP", style="blue")
    table.add_column("ISP", style="magenta")
    table.add_column("Created", style="yellow")

    for network in networks:
        status = network.status if hasattr(network, "status") else EeroNetworkStatus.UNKNOWN
        status_style = "green" if status == EeroNetworkStatus.ONLINE else "red"

        table.add_row(
            network.id,
            network.name,
            f"[{status_style}]{status}[/{status_style}]",
            network.public_ip or "Unknown",
            network.isp_name or "Unknown",
            (
                network.created_at.strftime("%Y-%m-%d")
                if hasattr(network, "created_at") and network.created_at
                else "Unknown"
            ),
        )

    return table


def print_network_details(network: Network) -> None:
    """Print detailed information about a network.

    Args:
        network: Network object
    """
    # Get network status
    status = network.status if hasattr(network, "status") else EeroNetworkStatus.UNKNOWN
    status_style = "green" if status == EeroNetworkStatus.ONLINE else "red"

    # Basic network info
    panel = Panel(
        f"[bold]Name:[/bold] {network.name}\n"
        f"[bold]Status:[/bold] [{status_style}]{status}[/{status_style}]\n"
        f"[bold]Public IP:[/bold] {network.public_ip or 'Unknown'}\n"
        f"[bold]ISP:[/bold] {network.isp_name or 'Unknown'}\n"
        f"[bold]Created:[/bold] {network.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(network, 'created_at') and network.created_at else 'Unknown'}\n"
        f"[bold]Updated:[/bold] {network.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(network, 'updated_at') and network.updated_at else 'Unknown'}\n"
        f"[bold]Guest Network:[/bold] {'Enabled' if hasattr(network, 'guest_network_enabled') and network.guest_network_enabled else 'Disabled'}\n",
        title=f"Network: {network.name}",
        border_style="blue",
    )
    console.print(panel)

    # DHCP information if available
    if hasattr(network, "dhcp") and network.dhcp:
        dhcp_panel = Panel(
            f"[bold]Subnet Mask:[/bold] {network.dhcp.subnet_mask}\n"
            f"[bold]Starting Address:[/bold] {network.dhcp.starting_address}\n"
            f"[bold]Ending Address:[/bold] {network.dhcp.ending_address}\n"
            f"[bold]Lease Time:[/bold] {network.dhcp.lease_time_seconds // 3600} hours\n"
            f"[bold]DNS Server:[/bold] {network.dhcp.dns_server or 'Default'}\n",
            title="DHCP Configuration",
            border_style="green",
        )
        console.print(dhcp_panel)

    # Settings information if available
    if hasattr(network, "settings") and network.settings:
        settings = network.settings
        settings_panel = Panel(
            f"[bold]IPv6 Upstream:[/bold] {'Enabled' if hasattr(settings, 'ipv6_upstream') and settings.ipv6_upstream else 'Disabled'}\n"
            f"[bold]IPv6 Downstream:[/bold] {'Enabled' if hasattr(settings, 'ipv6_downstream') and settings.ipv6_downstream else 'Disabled'}\n"
            f"[bold]Band Steering:[/bold] {'Enabled' if hasattr(settings, 'band_steering') and settings.band_steering else 'Disabled'}\n"
            f"[bold]Thread:[/bold] {'Enabled' if hasattr(settings, 'thread_enabled') and settings.thread_enabled else 'Disabled'}\n"
            f"[bold]UPnP:[/bold] {'Enabled' if hasattr(settings, 'upnp_enabled') and settings.upnp_enabled else 'Disabled'}\n"
            f"[bold]WPA3 Transition:[/bold] {'Enabled' if hasattr(settings, 'wpa3_transition') and settings.wpa3_transition else 'Disabled'}\n"
            f"[bold]DNS Caching:[/bold] {'Enabled' if hasattr(settings, 'dns_caching') and settings.dns_caching else 'Disabled'}\n",
            title="Network Settings",
            border_style="yellow",
        )
        console.print(settings_panel)

    # Speed test results if available
    if hasattr(network, "speed_test") and network.speed_test:
        speed_panel = Panel(
            f"[bold]Download:[/bold] {network.speed_test.get('down', {}).get('value', 0)} Mbps\n"
            f"[bold]Upload:[/bold] {network.speed_test.get('up', {}).get('value', 0)} Mbps\n"
            f"[bold]Latency:[/bold] {network.speed_test.get('latency', {}).get('value', 0)} ms\n"
            f"[bold]Tested:[/bold] {network.speed_test.get('date', 'Unknown')}\n",
            title="Speed Test Results",
            border_style="cyan",
        )
        console.print(speed_panel)
    else:
        console.print(
            "[yellow]No speed test results available. Run a speed test with: eero speedtest[/yellow]"
        )
