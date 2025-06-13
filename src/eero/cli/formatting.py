"""Formatting utilities for the Eero CLI."""

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..const import EeroDeviceStatus, EeroNetworkStatus
from ..models.device import Device
from ..models.eero import Eero
from ..models.network import Network
from ..models.profile import Profile

# Create console for rich output
console = Console()


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
        status_style = "green" if network.status == EeroNetworkStatus.ONLINE else "red"
        table.add_row(
            network.id,
            network.name,
            f"[{status_style}]{network.status}[/{status_style}]",
            network.public_ip or "Unknown",
            network.isp_name or "Unknown",
            (
                network.created_at.strftime("%Y-%m-%d")
                if network.created_at
                else "Unknown"
            ),
        )

    return table


def create_eeros_table(eeros: List[Eero]) -> Table:
    """Create a table displaying Eero devices.

    Args:
        eeros: List of Eero objects

    Returns:
        Rich Table object
    """
    table = Table(title="Eero Devices")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="blue")
    table.add_column("IP", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Type", style="magenta")
    table.add_column("Role", style="cyan")
    table.add_column("Connection", style="green")

    for eero in eeros:
        status_style = "green" if eero.connected else "red"
        role = []
        if eero.is_gateway:
            role.append("Gateway")
        if eero.is_primary:
            role.append("Primary")

        connection = "Wired" if eero.wired else "Wireless"
        if eero.backup_connection:
            connection += " (Backup)"

        table.add_row(
            eero.id,
            eero.name,
            eero.model,
            eero.ip_address or "Unknown",
            f"[{status_style}]{eero.status}[/{status_style}]",
            eero.device_type.value,
            ", ".join(role) if role else "Leaf",
            connection,
        )

    return table


def create_devices_table(devices: List[Device]) -> Table:
    """Create a table displaying network devices.

    Args:
        devices: List of Device objects

    Returns:
        Rich Table object
    """
    table = Table(title="Connected Devices")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Nickname", style="blue")
    table.add_column("IP", style="green")
    table.add_column("MAC", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Type", style="cyan")
    table.add_column("Manufacturer", style="green")

    for device in devices:
        status_style = "green"
        if device.status == EeroDeviceStatus.BLOCKED:
            status_style = "red"
        elif device.status == EeroDeviceStatus.DISCONNECTED:
            status_style = "yellow"

        table.add_row(
            device.id,
            device.name or "Unknown",
            device.nickname or "",
            device.ip_address or "Unknown",
            device.mac_address,
            f"[{status_style}]{device.status}[/{status_style}]",
            device.device_type or "Unknown",
            device.manufacturer or "Unknown",
        )

    return table


def create_profiles_table(profiles: List[Profile]) -> Table:
    """Create a table displaying profiles.

    Args:
        profiles: List of Profile objects

    Returns:
        Rich Table object
    """
    table = Table(title="Profiles")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Devices", style="blue")
    table.add_column("Connected", style="green")
    table.add_column("Paused", style="yellow")
    table.add_column("Schedule", style="magenta")
    table.add_column("Content Filter", style="cyan")

    for profile in profiles:
        paused_style = "red" if profile.paused else "green"
        schedule_status = "Enabled" if profile.schedule_enabled else "Disabled"
        content_filter_enabled = (
            "Enabled"
            if profile.content_filter and any(vars(profile.content_filter).values())
            else "Disabled"
        )

        table.add_row(
            profile.id,
            profile.name,
            str(profile.device_count),
            str(profile.connected_device_count),
            f"[{paused_style}]{'Yes' if profile.paused else 'No'}[/{paused_style}]",
            schedule_status,
            content_filter_enabled,
        )

    return table


def print_network_details(network: Network) -> None:
    """Print detailed information about a network.

    Args:
        network: Network object
    """
    panel = Panel(
        f"[bold]Name:[/bold] {network.name}\n"
        f"[bold]Status:[/bold] {network.status}\n"
        f"[bold]Public IP:[/bold] {network.public_ip or 'Unknown'}\n"
        f"[bold]ISP:[/bold] {network.isp_name or 'Unknown'}\n"
        f"[bold]Created:[/bold] {network.created_at.strftime('%Y-%m-%d %H:%M:%S') if network.created_at else 'Unknown'}\n"
        f"[bold]Updated:[/bold] {network.updated_at.strftime('%Y-%m-%d %H:%M:%S') if network.updated_at else 'Unknown'}\n"
        f"[bold]Guest Network:[/bold] {'Enabled' if network.guest_network_enabled else 'Disabled'}\n",
        title=f"Network: {network.name}",
        border_style="blue",
    )
    console.print(panel)

    # DHCP information
    if network.dhcp:
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

    # Settings
    settings_panel = Panel(
        f"[bold]IPv6 Upstream:[/bold] {'Enabled' if network.settings.ipv6_upstream else 'Disabled'}\n"
        f"[bold]IPv6 Downstream:[/bold] {'Enabled' if network.settings.ipv6_downstream else 'Disabled'}\n"
        f"[bold]Band Steering:[/bold] {'Enabled' if network.settings.band_steering else 'Disabled'}\n"
        f"[bold]Thread:[/bold] {'Enabled' if network.settings.thread_enabled else 'Disabled'}\n"
        f"[bold]UPnP:[/bold] {'Enabled' if network.settings.upnp_enabled else 'Disabled'}\n"
        f"[bold]WPA3 Transition:[/bold] {'Enabled' if network.settings.wpa3_transition else 'Disabled'}\n"
        f"[bold]DNS Caching:[/bold] {'Enabled' if network.settings.dns_caching else 'Disabled'}\n",
        title="Network Settings",
        border_style="yellow",
    )
    console.print(settings_panel)

    # Speed test results
    if network.speed_test:
        speed_panel = Panel(
            f"[bold]Download:[/bold] {network.speed_test.get('down', {}).get('value', 0)} Mbps\n"
            f"[bold]Upload:[/bold] {network.speed_test.get('up', {}).get('value', 0)} Mbps\n"
            f"[bold]Latency:[/bold] {network.speed_test.get('latency', {}).get('value', 0)} ms\n"
            f"[bold]Tested:[/bold] {network.speed_test.get('date', 'Unknown')}\n",
            title="Speed Test Results",
            border_style="cyan",
        )
        console.print(speed_panel)


def print_eero_details(eero: Eero) -> None:
    """Print detailed information about an Eero device.

    Args:
        eero: Eero object
    """
    status_style = "green" if eero.connected else "red"
    role = []
    if eero.is_gateway:
        role.append("Gateway")
    if eero.is_primary:
        role.append("Primary")

    connection = "Wired" if eero.wired else "Wireless"
    if eero.backup_connection:
        connection += " (Backup)"

    panel = Panel(
        f"[bold]Name:[/bold] {eero.name}\n"
        f"[bold]Model:[/bold] {eero.model}\n"
        f"[bold]Serial:[/bold] {eero.serial}\n"
        f"[bold]MAC Address:[/bold] {eero.mac_address}\n"
        f"[bold]IP Address:[/bold] {eero.ip_address or 'Unknown'}\n"
        f"[bold]Status:[/bold] [{status_style}]{eero.status}[/{status_style}]\n"
        f"[bold]Type:[/bold] {eero.device_type.value}\n"
        f"[bold]Role:[/bold] {', '.join(role) if role else 'Leaf'}\n"
        f"[bold]Connection:[/bold] {connection}\n"
        f"[bold]Connected Clients:[/bold] {eero.connected_clients_count}\n"
        f"[bold]Firmware:[/bold] {eero.firmware_version}\n"
        f"[bold]Uptime:[/bold] {eero.uptime // 86400 if eero.uptime else 0} days\n",
        title=f"Eero: {eero.name}",
        border_style="blue",
    )
    console.print(panel)

    # Health information
    if eero.health and eero.health.issues:
        health_panel = Panel(
            "\n".join(
                f"[bold]{issue.get('type', 'Issue')}:[/bold] {issue.get('description', 'No description')}"
                for issue in eero.health.issues
            ),
            title="Health Issues",
            border_style="red",
        )
        console.print(health_panel)

    # Location information
    if eero.location and (eero.location.address or eero.location.city):
        location_str = []
        if eero.location.address:
            location_str.append(eero.location.address)

        city_state = []
        if eero.location.city:
            city_state.append(eero.location.city)
        if eero.location.state:
            city_state.append(eero.location.state)

        if city_state:
            location_str.append(", ".join(city_state))

        if eero.location.zip_code:
            location_str.append(eero.location.zip_code)

        if eero.location.country:
            location_str.append(eero.location.country)

        location_panel = Panel(
            "\n".join(location_str),
            title="Location",
            border_style="yellow",
        )
        console.print(location_panel)


def print_device_details(device: Device) -> None:
    """Print detailed information about a device.

    Args:
        device: Device object
    """
    status_style = "green"
    if device.status == EeroDeviceStatus.BLOCKED:
        status_style = "red"
    elif device.status == EeroDeviceStatus.DISCONNECTED:
        status_style = "yellow"

    panel = Panel(
        f"[bold]Name:[/bold] {device.name or 'Unknown'}\n"
        f"[bold]Nickname:[/bold] {device.nickname or 'None'}\n"
        f"[bold]MAC Address:[/bold] {device.mac_address}\n"
        f"[bold]IP Address:[/bold] {device.ip_address or 'Unknown'}\n"
        f"[bold]Hostname:[/bold] {device.hostname or 'Unknown'}\n"
        f"[bold]Status:[/bold] [{status_style}]{device.status}[/{status_style}]\n"
        f"[bold]Manufacturer:[/bold] {device.manufacturer or 'Unknown'}\n"
        f"[bold]Model:[/bold] {device.model or 'Unknown'}\n"
        f"[bold]Type:[/bold] {device.device_type or 'Unknown'}\n"
        f"[bold]Connected:[/bold] {'Yes' if device.connected else 'No'}\n"
        f"[bold]Guest:[/bold] {'Yes' if device.guest else 'No'}\n"
        f"[bold]Paused:[/bold] {'Yes' if device.paused else 'No'}\n"
        f"[bold]Blocked:[/bold] {'Yes' if device.blocked else 'No'}\n"
        f"[bold]Profile:[/bold] {device.profile_id or 'None'}\n",
        title=f"Device: {device.name or device.nickname or device.hostname or 'Unknown'}",
        border_style="blue",
    )
    console.print(panel)

    # Connection details
    if device.connection:
        conn_panel = Panel(
            f"[bold]Type:[/bold] {device.connection.type}\n"
            f"[bold]Connected To:[/bold] {device.connection.connected_to or 'Unknown'}\n"
            f"[bold]Connected Via:[/bold] {device.connection.connected_via or 'Unknown'}\n"
            + (
                f"[bold]Frequency:[/bold] {device.connection.frequency}\n"
                if device.connection.frequency
                else ""
            )
            + (
                f"[bold]Signal Strength:[/bold] {device.connection.signal_strength}\n"
                if device.connection.signal_strength is not None
                else ""
            )
            + (
                f"[bold]TX Rate:[/bold] {device.connection.tx_rate} Mbps\n"
                if device.connection.tx_rate is not None
                else ""
            )
            + (
                f"[bold]RX Rate:[/bold] {device.connection.rx_rate} Mbps\n"
                if device.connection.rx_rate is not None
                else ""
            ),
            title="Connection Details",
            border_style="green",
        )
        console.print(conn_panel)

    # Tags
    if device.tags:
        tags_panel = Panel(
            "\n".join(
                f"[bold]{tag.name}:[/bold] {tag.color or 'No color'}"
                for tag in device.tags
            ),
            title="Tags",
            border_style="yellow",
        )
        console.print(tags_panel)


def print_profile_details(profile: Profile) -> None:
    """Print detailed information about a profile.

    Args:
        profile: Profile object
    """
    paused_style = "red" if profile.paused else "green"

    panel = Panel(
        f"[bold]Name:[/bold] {profile.name}\n"
        f"[bold]Devices:[/bold] {profile.device_count}\n"
        f"[bold]Connected Devices:[/bold] {profile.connected_device_count}\n"
        f"[bold]Paused:[/bold] [{paused_style}]{'Yes' if profile.paused else 'No'}[/{paused_style}]\n"
        f"[bold]Premium Enabled:[/bold] {'Yes' if profile.premium_enabled else 'No'}\n"
        f"[bold]Schedule Enabled:[/bold] {'Yes' if profile.schedule_enabled else 'No'}\n",
        title=f"Profile: {profile.name}",
        border_style="blue",
    )
    console.print(panel)

    # Schedule
    if profile.schedule_enabled and profile.schedule_blocks:
        schedule_panel = Panel(
            "\n".join(
                f"[bold]{', '.join(block.days)}:[/bold] {block.start_time} - {block.end_time}"
                for block in profile.schedule_blocks
            ),
            title="Schedule",
            border_style="green",
        )
        console.print(schedule_panel)

    # Content filter
    if profile.content_filter:
        content_filter = profile.content_filter
        filter_enabled = any(vars(content_filter).values())

        if filter_enabled:
            filter_settings = []
            for name, value in vars(content_filter).items():
                if value:
                    # Convert snake_case to title case for display
                    display_name = " ".join(
                        word.capitalize() for word in name.split("_")
                    )
                    filter_settings.append(f"[bold]{display_name}:[/bold] Enabled")

            filter_panel = Panel(
                "\n".join(filter_settings),
                title="Content Filtering",
                border_style="yellow",
            )
            console.print(filter_panel)

    # Block/Allow lists
    if profile.custom_block_list:
        block_panel = Panel(
            "\n".join(profile.custom_block_list),
            title="Blocked Domains",
            border_style="red",
        )
        console.print(block_panel)

    if profile.custom_allow_list:
        allow_panel = Panel(
            "\n".join(profile.custom_allow_list),
            title="Allowed Domains",
            border_style="green",
        )
        console.print(allow_panel)


def print_speedtest_results(result: dict) -> None:
    """Print speed test results.

    Args:
        result: Speed test result dictionary
    """
    # Format the results
    download = result.get("down", {}).get("value", 0)
    upload = result.get("up", {}).get("value", 0)
    latency = result.get("latency", {}).get("value", 0)

    speed_panel = Panel(
        f"[bold]Download:[/bold] {download} Mbps\n"
        f"[bold]Upload:[/bold] {upload} Mbps\n"
        f"[bold]Latency:[/bold] {latency} ms\n",
        title="Speed Test Results",
        border_style="green",
    )
    console.print(speed_panel)
