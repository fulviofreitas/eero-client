"""Formatting utilities for the Eero CLI."""

from typing import Any, Dict, List

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
        # Handle status formatting
        status_value = str(network.status)

        # Set appropriate status style and display text
        if status_value == "online" or status_value == "connected" or "ONLINE" in status_value:
            status_style = "green"
            display_status = "online"
        elif "OFFLINE" in status_value:
            status_style = "red"
            display_status = "offline"
        elif "UPDATING" in status_value:
            status_style = "yellow"
            display_status = "updating"
        else:
            status_style = "red"
            display_status = "unknown"

        table.add_row(
            network.id,
            network.name,
            f"[{status_style}]{display_status}[/{status_style}]",
            network.public_ip or "Unknown",
            network.isp_name or "Unknown",
            (network.created_at.strftime("%Y-%m-%d") if network.created_at else "Unknown"),
        )

    return table


def print_network_details(network: Network) -> None:
    """Print detailed information about a network.

    Args:
        network: Network object
    """
    # Handle status formatting
    status_value = str(network.status)

    # Set appropriate status style and display text
    if status_value == "online" or status_value == "connected" or "ONLINE" in status_value:
        status_style = "green"
        display_status = "online"
    elif "OFFLINE" in status_value:
        status_style = "red"
        display_status = "offline"
    elif "UPDATING" in status_value:
        status_style = "yellow"
        display_status = "updating"
    else:
        status_style = "red"
        display_status = "unknown"

    # Handle updated timestamp
    updated_display = "Unknown"
    if network.updated_at:
        updated_display = network.updated_at.strftime("%Y-%m-%d %H:%M:%S")

    panel = Panel(
        f"[bold]Name:[/bold] {network.name}\n"
        f"[bold]Status:[/bold] [{status_style}]{display_status}[/{status_style}]\n"
        f"[bold]Public IP:[/bold] {network.public_ip or 'Unknown'}\n"
        f"[bold]ISP:[/bold] {network.isp_name or 'Unknown'}\n"
        f"[bold]Created:[/bold] {network.created_at.strftime('%Y-%m-%d %H:%M:%S') if network.created_at else 'Unknown'}\n"
        f"[bold]Updated:[/bold] {updated_display}\n"
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
        f"[bold]IPv6 Upstream:[/bold] {'Enabled' if network.ipv6_upstream else 'Disabled'}\n"
        f"[bold]IPv6 Downstream:[/bold] {'Enabled' if network.settings.ipv6_downstream else 'Disabled'}\n"
        f"[bold]Band Steering:[/bold] {'Enabled' if network.band_steering else 'Disabled'}\n"
        f"[bold]Thread:[/bold] {'Enabled' if network.thread else 'Disabled'}\n"
        f"[bold]UPnP:[/bold] {'Enabled' if network.upnp else 'Disabled'}\n"
        f"[bold]WPA3 Transition:[/bold] {'Enabled' if network.settings.wpa3_transition else 'Disabled'}\n"
        f"[bold]DNS Caching:[/bold] {'Enabled' if (network.dns and network.dns.get('caching', False)) else 'Disabled'}\n"
        f"[bold]Wireless Mode:[/bold] {network.wireless_mode or 'Unknown'}\n"
        f"[bold]MLO Mode:[/bold] {network.mlo_mode or 'Unknown'}\n"
        f"[bold]SQM:[/bold] {'Enabled' if network.sqm else 'Disabled'}",
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

    # Resources
    resources = getattr(network, "resources", {})
    if resources:
        resources_panel = Panel(
            f"[bold]Available Resources:[/bold]\n"
            + "\n".join(f"  • {key}: {value}" for key, value in resources.items()),
            title="Available Resources",
            border_style="cyan",
        )
        console.print(resources_panel)


def print_network_details_extensive(network: Network) -> None:
    """Print extensive network information including all available fields.

    Args:
        network: Network object
    """
    # Handle status formatting
    status_value = str(network.status)

    # Set appropriate status style and display text
    if status_value == "online" or status_value == "connected" or "ONLINE" in status_value:
        status_style = "green"
        display_status = "online"
    elif "OFFLINE" in status_value:
        status_style = "red"
        display_status = "offline"
    elif "UPDATING" in status_value:
        status_style = "yellow"
        display_status = "updating"
    else:
        status_style = "red"
        display_status = "unknown"

    # Basic Network Information
    basic_panel = Panel(
        f"[bold]Name:[/bold] {network.name}\n"
        f"[bold]Display Name:[/bold] {network.display_name or 'N/A'}\n"
        f"[bold]Status:[/bold] [{status_style}]{display_status}[/{status_style}]\n"
        f"[bold]Public IP:[/bold] {network.public_ip or 'Unknown'}\n"
        f"[bold]ISP:[/bold] {network.isp_name or 'Unknown'}\n"
        f"[bold]Created:[/bold] {network.created_at.strftime('%Y-%m-%d %H:%M:%S') if network.created_at else 'Unknown'}\n"
        f"[bold]Updated:[/bold] {network.updated_at.strftime('%Y-%m-%d %H:%M:%S') if network.updated_at else 'Unknown'}\n"
        f"[bold]Owner:[/bold] {network.owner or 'Unknown'}\n"
        f"[bold]Network Type:[/bold] {network.network_customer_type or 'Unknown'}\n"
        f"[bold]Premium Status:[/bold] {network.premium_status or 'Unknown'}",
        title=f"Network: {network.name}",
        border_style="blue",
    )
    console.print(basic_panel)

    # Connection Information
    connection_panel = Panel(
        f"[bold]Gateway Type:[/bold] {network.gateway or 'Unknown'}\n"
        f"[bold]WAN Type:[/bold] {network.wan_type or 'Unknown'}\n"
        f"[bold]Gateway IP:[/bold] {network.gateway_ip or 'Unknown'}\n"
        f"[bold]Connection Mode:[/bold] {network.connection_mode or 'Unknown'}\n"
        f"[bold]Auto Setup Mode:[/bold] {network.auto_setup_mode or 'Unknown'}\n"
        f"[bold]Backup Internet:[/bold] {'Enabled' if network.backup_internet_enabled else 'Disabled'}\n"
        f"[bold]Power Saving:[/bold] {'Enabled' if network.power_saving else 'Disabled'}",
        title="Connection Information",
        border_style="green",
    )
    console.print(connection_panel)

    # Geographic Information
    geo_info = getattr(network, "geo_ip", {})
    if geo_info:
        geo_panel = Panel(
            f"[bold]Country:[/bold] {geo_info.get('countryName', 'Unknown')} ({geo_info.get('countryCode', 'Unknown')})\n"
            f"[bold]City:[/bold] {geo_info.get('city', 'Unknown')}\n"
            f"[bold]Region:[/bold] {geo_info.get('regionName', 'Unknown')}\n"
            f"[bold]Postal Code:[/bold] {geo_info.get('postalCode', 'Unknown')}\n"
            f"[bold]Timezone:[/bold] {geo_info.get('timezone', 'Unknown')}\n"
            f"[bold]Metro Code:[/bold] {geo_info.get('metroCode', 'Unknown')}\n"
            f"[bold]ASN:[/bold] {geo_info.get('asn', 'Unknown')}",
            title="Geographic Information",
            border_style="yellow",
        )
        console.print(geo_panel)

    # DHCP Configuration
    if network.dhcp:
        dhcp_panel = Panel(
            f"[bold]Subnet Mask:[/bold] {network.dhcp.subnet_mask}\n"
            f"[bold]Starting Address:[/bold] {network.dhcp.starting_address}\n"
            f"[bold]Ending Address:[/bold] {network.dhcp.ending_address}\n"
            f"[bold]Lease Time:[/bold] {network.dhcp.lease_time_seconds // 3600} hours\n"
            f"[bold]DNS Server:[/bold] {network.dhcp.dns_server or 'Default'}",
            title="DHCP Configuration",
            border_style="green",
        )
        console.print(dhcp_panel)

    # DNS Configuration
    dns_info = getattr(network, "dns", {})
    if dns_info:
        dns_panel = Panel(
            f"[bold]DNS Mode:[/bold] {dns_info.get('mode', 'Unknown')}\n"
            f"[bold]DNS Caching:[/bold] {'Enabled' if dns_info.get('caching', False) else 'Disabled'}\n"
            f"[bold]Parent DNS:[/bold] {', '.join(dns_info.get('parent', {}).get('ips', []))}\n"
            f"[bold]Custom DNS:[/bold] {', '.join(dns_info.get('custom', {}).get('ips', []))}",
            title="DNS Configuration",
            border_style="cyan",
        )
        console.print(dns_panel)

    # Network Settings
    settings_panel = Panel(
        f"[bold]IPv6 Upstream:[/bold] {'Enabled' if network.ipv6_upstream else 'Disabled'}\n"
        f"[bold]IPv6 Downstream:[/bold] {'Enabled' if network.settings.ipv6_downstream else 'Disabled'}\n"
        f"[bold]Band Steering:[/bold] {'Enabled' if network.band_steering else 'Disabled'}\n"
        f"[bold]Thread:[/bold] {'Enabled' if network.thread else 'Disabled'}\n"
        f"[bold]UPnP:[/bold] {'Enabled' if network.upnp else 'Disabled'}\n"
        f"[bold]WPA3 Transition:[/bold] {'Enabled' if network.settings.wpa3_transition else 'Disabled'}\n"
        f"[bold]DNS Caching:[/bold] {'Enabled' if (network.dns and network.dns.get('caching', False)) else 'Disabled'}\n"
        f"[bold]Wireless Mode:[/bold] {network.wireless_mode or 'Unknown'}\n"
        f"[bold]MLO Mode:[/bold] {network.mlo_mode or 'Unknown'}\n"
        f"[bold]SQM:[/bold] {'Enabled' if network.sqm else 'Disabled'}",
        title="Network Settings",
        border_style="yellow",
    )
    console.print(settings_panel)

    # Guest Network Information
    guest_panel = Panel(
        f"[bold]Guest Network:[/bold] {'Enabled' if network.guest_network_enabled else 'Disabled'}\n"
        f"[bold]Guest Network Name:[/bold] {network.guest_network_name or 'N/A'}\n"
        f"[bold]Guest Network Password:[/bold] {network.guest_network_password or 'N/A'}",
        title="Guest Network",
        border_style="magenta",
    )
    console.print(guest_panel)

    # Speed Test Results
    if network.speed_test:
        speed_panel = Panel(
            f"[bold]Download:[/bold] {network.speed_test.get('down', {}).get('value', 0)} Mbps\n"
            f"[bold]Upload:[/bold] {network.speed_test.get('up', {}).get('value', 0)} Mbps\n"
            f"[bold]Latency:[/bold] {network.speed_test.get('latency', {}).get('value', 0)} ms\n"
            f"[bold]Tested:[/bold] {network.speed_test.get('date', 'Unknown')}\n"
            f"[bold]Status:[/bold] {network.speed_test.get('status', 'Unknown')}",
            title="Speed Test Results",
            border_style="cyan",
        )
        console.print(speed_panel)

    # Health Information
    health_info = getattr(network, "health", {})
    if health_info:
        health_panel = Panel(
            f"[bold]Internet Status:[/bold] {health_info.get('internet', {}).get('status', 'Unknown')}\n"
            f"[bold]ISP Up:[/bold] {'Yes' if health_info.get('internet', {}).get('isp_up', False) else 'No'}\n"
            f"[bold]Eero Network Status:[/bold] {health_info.get('eero_network', {}).get('status', 'Unknown')}",
            title="Network Health",
            border_style="green",
        )
        console.print(health_panel)

    # Organization Information
    org_info = getattr(network, "organization", {})
    if org_info:
        org_panel = Panel(
            f"[bold]Organization ID:[/bold] {org_info.get('id', 'Unknown')}\n"
            f"[bold]Organization Name:[/bold] {org_info.get('name', 'Unknown')}\n"
            f"[bold]Organization Brand:[/bold] {org_info.get('brand', 'Unknown')}\n"
            f"[bold]Organization Type:[/bold] {org_info.get('type', 'Unknown')}",
            title="Organization",
            border_style="blue",
        )
        console.print(org_panel)

    # Premium Details
    premium_info = getattr(network, "premium_details", {})
    if premium_info:
        premium_panel = Panel(
            f"[bold]Tier:[/bold] {premium_info.get('tier', 'Unknown')}\n"
            f"[bold]Payment Method:[/bold] {premium_info.get('payment_method', 'Unknown')}\n"
            f"[bold]Interval:[/bold] {premium_info.get('interval', 'Unknown')}\n"
            f"[bold]Next Billing:[/bold] {premium_info.get('next_billing_event_date', 'Unknown')}\n"
            f"[bold]My Subscription:[/bold] {'Yes' if premium_info.get('is_my_subscription', False) else 'No'}\n"
            f"[bold]Has Payment Info:[/bold] {'Yes' if premium_info.get('has_payment_info', False) else 'No'}",
            title="Premium Details",
            border_style="magenta",
        )
        console.print(premium_panel)

    # Updates Information
    updates_info = getattr(network, "updates", {})
    if updates_info:
        updates_panel = Panel(
            f"[bold]Update Required:[/bold] {'Yes' if updates_info.get('update_required', False) else 'No'}\n"
            f"[bold]Can Update Now:[/bold] {'Yes' if updates_info.get('can_update_now', False) else 'No'}\n"
            f"[bold]Has Update:[/bold] {'Yes' if updates_info.get('has_update', False) else 'No'}\n"
            f"[bold]Target Firmware:[/bold] {updates_info.get('target_firmware', 'Unknown')}\n"
            f"[bold]Min Required Firmware:[/bold] {updates_info.get('min_required_firmware', 'Unknown')}\n"
            f"[bold]Preferred Update Hour:[/bold] {updates_info.get('preferred_update_hour', 'Unknown')}\n"
            f"[bold]Last Update Started:[/bold] {updates_info.get('last_update_started', 'Unknown')}",
            title="Updates",
            border_style="yellow",
        )
        console.print(updates_panel)

    # DDNS Information
    ddns_info = getattr(network, "ddns", {})
    if ddns_info:
        ddns_panel = Panel(
            f"[bold]DDNS Enabled:[/bold] {'Yes' if ddns_info.get('enabled', False) else 'No'}\n"
            f"[bold]Subdomain:[/bold] {ddns_info.get('subdomain', 'Unknown')}",
            title="DDNS",
            border_style="cyan",
        )
        console.print(ddns_panel)

    # HomeKit Information
    homekit_info = getattr(network, "homekit", {})
    if homekit_info:
        homekit_panel = Panel(
            f"[bold]HomeKit Enabled:[/bold] {'Yes' if homekit_info.get('enabled', False) else 'No'}\n"
            f"[bold]Managed Network Enabled:[/bold] {'Yes' if homekit_info.get('managedNetworkEnabled', False) else 'No'}\n"
            f"[bold]Enabled Last Changed:[/bold] {homekit_info.get('enabledLastChanged', 'Unknown')}",
            title="HomeKit",
            border_style="green",
        )
        console.print(homekit_panel)

    # Amazon Integration
    amazon_panel = Panel(
        f"[bold]Amazon Account Linked:[/bold] {'Yes' if getattr(network, 'amazon_account_linked', False) else 'No'}\n"
        f"[bold]FFS:[/bold] {'Yes' if getattr(network, 'ffs', False) else 'No'}\n"
        f"[bold]Alexa Skill:[/bold] {'Yes' if getattr(network, 'alexa_skill', False) else 'No'}\n"
        f"[bold]Amazon Device Nickname:[/bold] {'Yes' if getattr(network, 'amazon_device_nickname', False) else 'No'}",
        title="Amazon Integration",
        border_style="blue",
    )
    console.print(amazon_panel)

    # IP Settings
    ip_settings = getattr(network, "ip_settings", {})
    if ip_settings:
        ip_panel = Panel(
            f"[bold]Double NAT:[/bold] {'Yes' if ip_settings.get('double_nat', False) else 'No'}\n"
            f"[bold]Public IP:[/bold] {ip_settings.get('public_ip', 'Unknown')}",
            title="IP Settings",
            border_style="yellow",
        )
        console.print(ip_panel)

    # Premium DNS
    premium_dns = getattr(network, "premium_dns", {})
    if premium_dns:
        dns_policies = premium_dns.get("dns_policies", {})
        ad_block_settings = premium_dns.get("ad_block_settings", {})

        premium_dns_panel = Panel(
            f"[bold]DNS Policies Enabled:[/bold] {'Yes' if premium_dns.get('dns_policies_enabled', False) else 'No'}\n"
            f"[bold]DNS Provider:[/bold] {premium_dns.get('dns_provider', 'Unknown')}\n"
            f"[bold]Block Malware:[/bold] {'Yes' if dns_policies.get('block_malware', False) else 'No'}\n"
            f"[bold]Ad Block:[/bold] {'Yes' if dns_policies.get('ad_block', False) else 'No'}\n"
            f"[bold]Ad Block Enabled:[/bold] {'Yes' if ad_block_settings.get('enabled', False) else 'No'}",
            title="Premium DNS",
            border_style="magenta",
        )
        console.print(premium_dns_panel)

    # Last Reboot Information
    last_reboot = getattr(network, "last_reboot", None)
    if last_reboot:
        reboot_panel = Panel(
            f"[bold]Last Reboot:[/bold] {last_reboot}",
            title="Last Reboot",
            border_style="red",
        )
        console.print(reboot_panel)

    # Resources
    resources = getattr(network, "resources", {})
    if resources:
        resources_panel = Panel(
            f"[bold]Available Resources:[/bold]\n"
            + "\n".join(f"  • {key}: {value}" for key, value in resources.items()),
            title="Available Resources",
            border_style="cyan",
        )
        console.print(resources_panel)


def create_eeros_table(eeros: List[Eero]) -> Table:
    """Create a table displaying Eero devices.

    Args:
        eeros: List of Eero objects

    Returns:
        Rich Table object
    """
    table = Table(title="Eero Devices")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Model", style="green")
    table.add_column("IP", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Type", style="red")
    table.add_column("Role", style="white")
    table.add_column("Connection", style="green")

    for eero in eeros:
        # Get Eero ID from URL
        eero_id = eero.eero_id if hasattr(eero, "eero_id") else ""

        # Use location as name
        eero_name = str(eero.location) if eero.location else ""

        # Determine type based on is_primary_node field
        device_type = "Primary" if eero.is_primary_node else "Secondary"

        # Determine role based on gateway field
        role = "Gateway" if eero.gateway else "Leaf"

        # Color-code the status
        status_color = "green" if eero.status == "green" else "red"
        status_display = f"[{status_color}]{eero.status}[/{status_color}]"

        table.add_row(
            eero_id,
            eero_name,
            eero.model,
            eero.ip_address or "",
            status_display,
            device_type,
            role,
            eero.connection_type or "Unknown",
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
    table.add_column("Connection Type", style="blue")
    table.add_column("Eero Location", style="yellow")
    table.add_column("Interface", style="cyan")

    for device in devices:
        # Determine status style and display text
        if device.status == EeroDeviceStatus.CONNECTED:
            status_style = "green"
            status_text = "connected"
        elif device.status == EeroDeviceStatus.BLOCKED:
            status_style = "red"
            status_text = "blocked"
        elif device.status == EeroDeviceStatus.DISCONNECTED:
            status_style = "yellow"
            status_text = "disconnected"
        else:
            status_style = "dim"
            status_text = "unknown"

        # Use display_name, hostname, or nickname as the name
        device_name = device.display_name or device.hostname or device.nickname or "Unknown"

        # Use primary IP address
        ip_address = device.ip or device.ipv4 or "Unknown"

        # Use MAC address
        mac_address = device.mac or "Unknown"

        # Connection type
        connection_type = device.connection_type or "Unknown"

        # Eero source location
        eero_location = device.source.location if device.source else "Unknown"

        # Interface information
        interface_info = ""
        if device.interface:
            if device.interface.frequency and device.interface.frequency_unit:
                interface_info = f"{device.interface.frequency} {device.interface.frequency_unit}"
            elif device.interface.frequency:
                interface_info = f"{device.interface.frequency} GHz"
        elif device.connectivity and device.connectivity.frequency:
            # Fallback to connectivity frequency if interface not available
            interface_info = f"{device.connectivity.frequency} MHz"

        table.add_row(
            device.id or "Unknown",
            device_name,
            device.nickname or "",
            ip_address,
            mac_address,
            f"[{status_style}]{status_text}[/{status_style}]",
            device.device_type or "Unknown",
            device.manufacturer or "Unknown",
            connection_type,
            eero_location,
            interface_info or "Unknown",
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
    table.add_column("State", style="green")
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

        # Get state value
        state_value = profile.state.value if profile.state else "Unknown"

        table.add_row(
            profile.id or "N/A",
            profile.name,
            state_value,
            f"[{paused_style}]{'Yes' if profile.paused else 'No'}[/{paused_style}]",
            schedule_status,
            content_filter_enabled,
        )

    return table


def print_eero_details(eero: Eero) -> None:
    """Print detailed information about an Eero device.

    Args:
        eero: Eero object
    """
    # Determine role based on gateway field
    role = "Gateway" if eero.gateway else "Leaf"

    # Determine type based on is_primary_node field
    device_type = "Primary" if eero.is_primary_node else "Secondary"

    # Get Eero ID from URL
    eero_id = eero.eero_id if hasattr(eero, "eero_id") else "Unknown"

    # Use location as name
    eero_name = str(eero.location) if eero.location else ""

    # Color-code the status
    status_color = "green" if eero.status == "green" else "red"
    status_display = f"[{status_color}]{eero.status}[/{status_color}]"

    panel = Panel(
        f"[bold]ID:[/bold] {eero_id}\n"
        f"[bold]Name:[/bold] {eero_name}\n"
        f"[bold]Model:[/bold] {eero.model}\n"
        f"[bold]Serial:[/bold] {eero.serial}\n"
        f"[bold]MAC Address:[/bold] {eero.mac_address}\n"
        f"[bold]IP Address:[/bold] {eero.ip_address or 'Unknown'}\n"
        f"[bold]Status:[/bold] {status_display}\n"
        f"[bold]Type:[/bold] {device_type}\n"
        f"[bold]Role:[/bold] {role}\n"
        f"[bold]Connection:[/bold] {eero.connection_type or 'Unknown'}\n"
        f"[bold]Connected Clients:[/bold] {eero.connected_clients_count}\n"
        f"[bold]Firmware:[/bold] {eero.os or 'Unknown'}\n"
        f"[bold]Uptime:[/bold] {eero.uptime or 0} days",
        title=f"Eero: {eero_name}",
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
    if eero.location:
        if isinstance(eero.location, str):
            # Location is a simple string
            location_panel = Panel(
                eero.location,
                title="Location",
                border_style="yellow",
            )
            console.print(location_panel)
        elif hasattr(eero.location, "address") and (eero.location.address or eero.location.city):
            # Location is a Location object with address/city
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
    status_text = "connected"
    if device.status == EeroDeviceStatus.BLOCKED:
        status_style = "red"
        status_text = "blocked"
    elif device.status == EeroDeviceStatus.DISCONNECTED:
        status_style = "yellow"
        status_text = "disconnected"

    device_name = device.display_name or device.hostname or device.nickname or "Unknown"
    ip_address = device.ip or device.ipv4 or "Unknown"
    mac_address = device.mac or "Unknown"

    # Profile display: name (id)
    profile_display = "None"
    if device.profile:
        profile_name = device.profile.name or "Unknown"
        profile_id = device.profile_id or "Unknown"
        profile_display = f"{profile_name} ({profile_id})"
    elif device.profile_id:
        profile_display = f"Unknown ({device.profile_id})"

    panel = Panel(
        f"[bold]Name:[/bold] {device_name}\n"
        f"[bold]Nickname:[/bold] {device.nickname or 'None'}\n"
        f"[bold]MAC Address:[/bold] {mac_address}\n"
        f"[bold]IP Address:[/bold] {ip_address}\n"
        f"[bold]Hostname:[/bold] {device.hostname or 'Unknown'}\n"
        f"[bold]Status:[/bold] [{status_style}]{status_text}[/{status_style}]\n"
        f"[bold]Manufacturer:[/bold] {device.manufacturer or 'Unknown'}\n"
        f"[bold]Model:[/bold] {device.model_name or 'Unknown'}\n"
        f"[bold]Type:[/bold] {device.device_type or 'Unknown'}\n"
        f"[bold]Connected:[/bold] {'Yes' if device.connected else 'No'}\n"
        f"[bold]Guest:[/bold] {'Yes' if device.is_guest else 'No'}\n"
        f"[bold]Paused:[/bold] {'Yes' if device.paused else 'No'}\n"
        f"[bold]Blocked:[/bold] {'Yes' if device.blacklisted else 'No'}\n"
        f"[bold]Profile:[/bold] {profile_display}\n"
        f"[bold]Connection Type:[/bold] {device.connection_type or 'Unknown'}\n",
        title=f"Device: {device_name}",
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
            "\n".join(f"[bold]{tag.name}:[/bold] {tag.color or 'No color'}" for tag in device.tags),
            title="Tags",
            border_style="yellow",
        )
        console.print(tags_panel)


def create_profile_devices_table(devices: List[Dict[str, Any]]) -> Table:
    """Create a table displaying devices in a profile.

    Args:
        devices: List of device dictionaries from profile

    Returns:
        Rich Table object
    """
    table = Table(title="Profile Devices")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Nickname", style="blue")
    table.add_column("IP", style="green")
    table.add_column("MAC", style="yellow")
    table.add_column("Connected", style="magenta")
    table.add_column("Type", style="cyan")
    table.add_column("Manufacturer", style="green")
    table.add_column("Connection Type", style="blue")
    table.add_column("Eero Location", style="yellow")

    for device in devices:
        # Extract device ID from URL
        device_id = "Unknown"
        if device.get("url"):
            parts = device["url"].split("/")
            if len(parts) >= 2:
                device_id = parts[-1]

        # Use display_name, hostname, or nickname as the name
        device_name = (
            device.get("display_name")
            or device.get("hostname")
            or device.get("nickname")
            or "Unknown"
        )

        # Use primary IP address
        ip_address = device.get("ip") or "Unknown"

        # Use MAC address
        mac_address = device.get("mac") or "Unknown"

        # Connection status
        connected = device.get("connected", False)
        connected_style = "green" if connected else "red"
        connected_text = "Yes" if connected else "No"

        # Connection type
        connection_type = device.get("connection_type") or "Unknown"

        # Eero source location
        source = device.get("source", {})
        eero_location = source.get("location") if source else "Unknown"

        table.add_row(
            device_id,
            device_name,
            device.get("nickname") or "",
            ip_address,
            mac_address,
            f"[{connected_style}]{connected_text}[/{connected_style}]",
            device.get("device_type") or "Unknown",
            device.get("manufacturer") or "Unknown",
            connection_type,
            eero_location,
        )

    return table


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
                    display_name = " ".join(word.capitalize() for word in name.split("_"))
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


def print_profile_details_brief(profile: Profile) -> None:
    """Print brief profile information with devices table.

    Args:
        profile: Profile object
    """
    paused_style = "red" if profile.paused else "green"

    # Profile summary panel
    panel = Panel(
        f"[bold]Name:[/bold] {profile.name}\n"
        f"[bold]State:[/bold] {profile.state.value if profile.state else 'Unknown'}\n"
        f"[bold]Paused:[/bold] [{paused_style}]{'Yes' if profile.paused else 'No'}[/{paused_style}]\n"
        f"[bold]Schedule:[/bold] {'Enabled' if profile.schedule_enabled else 'Disabled'}\n"
        f"[bold]Content Filter:[/bold] {'Enabled' if profile.content_filter and any(vars(profile.content_filter).values()) else 'Disabled'}",
        title=f"Profile: {profile.name}",
        border_style="blue",
    )
    console.print(panel)

    # Devices table
    if profile.devices:
        devices_table = create_profile_devices_table(profile.devices)
        console.print(devices_table)
    else:
        console.print("[bold yellow]No devices in this profile[/bold yellow]")


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


def print_eero_details_extensive(eero: Eero) -> None:
    """Print extensive Eero device information including all available fields.

    Args:
        eero: Eero object
    """
    # Get Eero ID from URL
    eero_id = eero.eero_id if hasattr(eero, "eero_id") else "Unknown"

    # Use location as name
    eero_name = str(eero.location) if eero.location else ""

    # Color-code the status
    status_color = "green" if eero.status == "green" else "red"
    status_display = f"[{status_color}]{eero.status}[/{status_color}]"

    # Basic Device Information
    basic_panel = Panel(
        f"[bold]ID:[/bold] {eero_id}\n"
        f"[bold]Name:[/bold] {eero_name}\n"
        f"[bold]Model:[/bold] {eero.model}\n"
        f"[bold]Model Number:[/bold] {getattr(eero, 'model_number', 'Unknown')}\n"
        f"[bold]Model Variant:[/bold] {getattr(eero, 'model_variant', 'N/A')}\n"
        f"[bold]Serial:[/bold] {eero.serial}\n"
        f"[bold]MAC Address:[/bold] {eero.mac_address}\n"
        f"[bold]IP Address:[/bold] {eero.ip_address or 'Unknown'}\n"
        f"[bold]Status:[/bold] {status_display}\n"
        f"[bold]State:[/bold] {getattr(eero, 'state', 'Unknown')}\n"
        f"[bold]Type:[/bold] {'Primary' if eero.is_primary_node else 'Secondary'}\n"
        f"[bold]Role:[/bold] {'Gateway' if eero.gateway else 'Leaf'}\n"
        f"[bold]Connection:[/bold] {eero.connection_type or 'Unknown'}\n"
        f"[bold]Wired:[/bold] {'Yes' if getattr(eero, 'wired', False) else 'No'}\n"
        f"[bold]Using WAN:[/bold] {'Yes' if getattr(eero, 'using_wan', False) else 'No'}",
        title=f"Eero: {eero_name}",
        border_style="blue",
    )
    console.print(basic_panel)

    # Network Information
    network_info = getattr(eero, "network", {})
    if network_info:
        network_panel = Panel(
            f"[bold]Network Name:[/bold] {network_info.get('name', 'Unknown')}\n"
            f"[bold]Network URL:[/bold] {network_info.get('url', 'Unknown')}\n"
            f"[bold]Network Created:[/bold] {network_info.get('created', 'Unknown')}",
            title="Network Information",
            border_style="green",
        )
        console.print(network_panel)

    # Timing Information
    timing_panel = Panel(
        f"[bold]Joined:[/bold] {getattr(eero, 'joined', 'Unknown')}\n"
        f"[bold]Last Reboot:[/bold] {getattr(eero, 'last_reboot', 'Unknown')}\n"
        f"[bold]Last Heartbeat:[/bold] {getattr(eero, 'last_heartbeat', 'Unknown')}\n"
        f"[bold]Heartbeat OK:[/bold] {'Yes' if getattr(eero, 'heartbeat_ok', False) else 'No'}",
        title="Timing Information",
        border_style="yellow",
    )
    console.print(timing_panel)

    # Firmware Information
    firmware_panel = Panel(
        f"[bold]OS:[/bold] {eero.os or 'Unknown'}\n"
        f"[bold]OS Version:[/bold] {getattr(eero, 'os_version', 'Unknown')}\n"
        f"[bold]Update Available:[/bold] {'Yes' if getattr(eero, 'update_available', False) else 'No'}",
        title="Firmware Information",
        border_style="cyan",
    )
    console.print(firmware_panel)

    # Update Status
    update_status = getattr(eero, "update_status", None)
    if update_status:
        update_panel = Panel(
            f"[bold]Support Expired:[/bold] {'Yes' if getattr(update_status, 'support_expired', False) else 'No'}\n"
            f"[bold]Support Expiration String:[/bold] {getattr(update_status, 'support_expiration_string', 'N/A')}\n"
            f"[bold]Support Expiration Date:[/bold] {getattr(update_status, 'support_expiration_date', 'N/A')}",
            title="Update Status",
            border_style="magenta",
        )
        console.print(update_panel)

    # Client Information
    client_panel = Panel(
        f"[bold]Connected Clients:[/bold] {eero.connected_clients_count}\n"
        f"[bold]Wired Clients:[/bold] {getattr(eero, 'connected_wired_clients_count', 0)}\n"
        f"[bold]Wireless Clients:[/bold] {getattr(eero, 'connected_wireless_clients_count', 0)}",
        title="Client Information",
        border_style="blue",
    )
    console.print(client_panel)

    # LED Information
    led_panel = Panel(
        f"[bold]LED On:[/bold] {'Yes' if getattr(eero, 'led_on', False) else 'No'}\n"
        f"[bold]LED Brightness:[/bold] {getattr(eero, 'led_brightness', 0)}%",
        title="LED Information",
        border_style="green",
    )
    console.print(led_panel)

    # Power Information
    power_info = getattr(eero, "power_info", None)
    if power_info:
        power_panel = Panel(
            f"[bold]Power Source:[/bold] {getattr(power_info, 'power_source', 'Unknown')}\n"
            f"[bold]Power Source Metadata:[/bold] {getattr(power_info, 'power_source_metadata', {})}",
            title="Power Information",
            border_style="yellow",
        )
        console.print(power_panel)

    # Mesh Information
    mesh_panel = Panel(
        f"[bold]Mesh Quality Bars:[/bold] {getattr(eero, 'mesh_quality_bars', 0)}/5\n"
        f"[bold]Auto Provisioned:[/bold] {'Yes' if getattr(eero, 'auto_provisioned', False) else 'No'}\n"
        f"[bold]Provides WiFi:[/bold] {'Yes' if getattr(eero, 'provides_wifi', False) else 'No'}",
        title="Mesh Information",
        border_style="cyan",
    )
    console.print(mesh_panel)

    # WiFi Information
    wifi_bssids = getattr(eero, "wifi_bssids", [])
    if wifi_bssids:
        wifi_panel = Panel(
            f"[bold]WiFi BSSIDs:[/bold]\n" + "\n".join(f"  • {bssid}" for bssid in wifi_bssids),
            title="WiFi BSSIDs",
            border_style="magenta",
        )
        console.print(wifi_panel)

    # Bands Information
    bands = getattr(eero, "bands", [])
    if bands:
        bands_panel = Panel(
            f"[bold]Supported Bands:[/bold]\n" + "\n".join(f"  • {band}" for band in bands),
            title="Supported Bands",
            border_style="blue",
        )
        console.print(bands_panel)

    # BSSIDs with Bands
    bssids_with_bands = getattr(eero, "bssids_with_bands", [])
    if bssids_with_bands:
        bssids_bands_panel = Panel(
            f"[bold]BSSIDs with Bands:[/bold]\n"
            + "\n".join(
                f"  • {getattr(item, 'band', 'Unknown')}: {getattr(item, 'ethernet_address', 'Unknown')}"
                for item in bssids_with_bands
            ),
            title="BSSIDs with Bands",
            border_style="green",
        )
        console.print(bssids_bands_panel)

    # Ethernet Information
    ethernet_addresses = getattr(eero, "ethernet_addresses", [])
    if ethernet_addresses:
        ethernet_panel = Panel(
            f"[bold]Ethernet Addresses:[/bold]\n"
            + "\n".join(f"  • {addr}" for addr in ethernet_addresses),
            title="Ethernet Addresses",
            border_style="yellow",
        )
        console.print(ethernet_panel)

    # Port Details
    port_details = getattr(eero, "port_details", [])
    if port_details:
        port_panel = Panel(
            f"[bold]Port Details:[/bold]\n"
            + "\n".join(
                f"  • Port {getattr(item, 'port_name', 'Unknown')} ({getattr(item, 'position', 'Unknown')}): {getattr(item, 'ethernet_address', 'Unknown')}"
                for item in port_details
            ),
            title="Port Details",
            border_style="cyan",
        )
        console.print(port_panel)

    # IPv6 Addresses
    ipv6_addresses = getattr(eero, "ipv6_addresses", [])
    if ipv6_addresses:
        ipv6_panel = Panel(
            f"[bold]IPv6 Addresses:[/bold]\n"
            + "\n".join(
                f"  • {getattr(addr, 'address', 'Unknown')} ({getattr(addr, 'scope', 'Unknown')}) - {getattr(addr, 'interface', 'Unknown')}"
                for addr in ipv6_addresses
            ),
            title="IPv6 Addresses",
            border_style="magenta",
        )
        console.print(ipv6_panel)

    # Organization Information
    organization = getattr(eero, "organization", None)
    if organization:
        org_panel = Panel(
            f"[bold]Organization ID:[/bold] {getattr(organization, 'id', 'Unknown')}\n"
            f"[bold]Organization Name:[/bold] {getattr(organization, 'name', 'Unknown')}",
            title="Organization",
            border_style="blue",
        )
        console.print(org_panel)

    # Ethernet Status
    ethernet_status = getattr(eero, "ethernet_status", None)
    if ethernet_status:
        statuses = getattr(ethernet_status, "statuses", [])
        if statuses:
            ethernet_panel = Panel(
                f"[bold]Ethernet Status:[/bold]\n"
                + "\n".join(
                    f"  • Port {getattr(status, 'port_name', 'Unknown')}: "
                    f"{'Connected' if getattr(status, 'hasCarrier', False) else 'Disconnected'} "
                    f"({getattr(status, 'speed', 'Unknown')})"
                    for status in statuses
                ),
                title="Ethernet Status",
                border_style="green",
            )
            console.print(ethernet_panel)

    # Neighbor Information (from ethernet status)
    if ethernet_status:
        statuses = getattr(ethernet_status, "statuses", [])
        neighbors = []
        for status in statuses:
            neighbor = getattr(status, "neighbor", None)
            if neighbor:
                neighbor_type = getattr(neighbor, "type", "Unknown")
                metadata = getattr(neighbor, "metadata", {})
                if metadata:
                    port = getattr(metadata, "port", "Unknown")
                    port_name = getattr(metadata, "port_name", "Unknown")
                    location = getattr(metadata, "location", "Unknown")
                    url = getattr(metadata, "url", "Unknown")
                    neighbors.append(
                        f"  • {neighbor_type} - Port {port_name} ({port}) at {location}"
                    )

        if neighbors:
            neighbor_panel = Panel(
                f"[bold]Neighbors:[/bold]\n" + "\n".join(neighbors),
                title="Neighbor Information",
                border_style="blue",
            )
            console.print(neighbor_panel)

    # LLDP Information
    if ethernet_status:
        statuses = getattr(ethernet_status, "statuses", [])
        lldp_info = []
        for status in statuses:
            lldp_list = getattr(status, "lldpInfo", [])
            for lldp in lldp_list:
                system_name = getattr(lldp, "systemName", "Unknown")
                system_desc = getattr(lldp, "systemDescription", "Unknown")
                chassis_id = getattr(lldp, "chassisId", "Unknown")
                port_id = getattr(lldp, "portId", "Unknown")
                port_desc = getattr(lldp, "portDescription", "Unknown")
                mac_address = getattr(lldp, "macAddress", "Unknown")
                mgmt_ipv4 = getattr(lldp, "managementIpv4Address", "Unknown")

                lldp_info.append(
                    f"  • {system_name} ({system_desc})\n"
                    f"    Chassis: {chassis_id}, Port: {port_id} ({port_desc})\n"
                    f"    MAC: {mac_address}, Management IP: {mgmt_ipv4}"
                )

        if lldp_info:
            lldp_panel = Panel(
                f"[bold]LLDP Information:[/bold]\n" + "\n".join(lldp_info),
                title="LLDP Information",
                border_style="yellow",
            )
            console.print(lldp_panel)

    # Additional Features
    features_panel = Panel(
        f"[bold]Requires Amazon Pre-authorized Code:[/bold] {'Yes' if getattr(eero, 'requires_amazon_pre_authorized_code', False) else 'No'}\n"
        f"[bold]Extended Border Agent Address:[/bold] {getattr(eero, 'extended_border_agent_address', 'N/A')}\n"
        f"[bold]Provide Device Power:[/bold] {getattr(eero, 'provide_device_power', 'N/A')}\n"
        f"[bold]Backup WAN:[/bold] {getattr(eero, 'backup_wan', 'N/A')}\n"
        f"[bold]Wireless Upstream Node:[/bold] {getattr(eero, 'wireless_upstream_node', 'N/A')}\n"
        f"[bold]Cellular Backup:[/bold] {getattr(eero, 'cellular_backup', 'N/A')}\n"
        f"[bold]Channel Selection:[/bold] {getattr(eero, 'channel_selection', 'N/A')}\n"
        f"[bold]Nightlight:[/bold] {getattr(eero, 'nightlight', 'N/A')}",
        title="Additional Features",
        border_style="magenta",
    )
    console.print(features_panel)

    # Resources
    resources = getattr(eero, "resources", {})
    if resources:
        resources_panel = Panel(
            f"[bold]Available Resources:[/bold]\n"
            + "\n".join(f"  • {key}: {value}" for key, value in resources.items()),
            title="Available Resources",
            border_style="blue",
        )
        console.print(resources_panel)

    # Messages
    messages = getattr(eero, "messages", [])
    if messages:
        messages_panel = Panel(
            f"[bold]Messages:[/bold]\n" + "\n".join(f"  • {msg}" for msg in messages),
            title="Messages",
            border_style="red",
        )
        console.print(messages_panel)


def print_device_details_extensive(device: Device) -> None:
    """Print extensive device information including all available fields.

    Args:
        device: Device object
    """
    status_style = "green"
    status_text = "connected"
    if device.status == EeroDeviceStatus.BLOCKED:
        status_style = "red"
        status_text = "blocked"
    elif device.status == EeroDeviceStatus.DISCONNECTED:
        status_style = "yellow"
        status_text = "disconnected"

    device_name = device.display_name or device.hostname or device.nickname or "Unknown"
    ip_address = device.ip or device.ipv4 or "Unknown"
    mac_address = device.mac or "Unknown"
    profile_name = device.profile.name if device.profile else "None"

    # Profile display: name (id)
    profile_display = "None"
    if device.profile:
        profile_name = device.profile.name or "Unknown"
        profile_id = device.profile_id or "Unknown"
        profile_display = f"{profile_name} ({profile_id})"
    elif device.profile_id:
        profile_display = f"Unknown ({device.profile_id})"

    # Basic Device Information
    panel = Panel(
        f"[bold]Name:[/bold] {device_name}\n"
        f"[bold]Nickname:[/bold] {device.nickname or 'None'}\n"
        f"[bold]MAC Address:[/bold] {mac_address}\n"
        f"[bold]IP Address:[/bold] {ip_address}\n"
        f"[bold]Hostname:[/bold] {device.hostname or 'Unknown'}\n"
        f"[bold]Status:[/bold] [{status_style}]{status_text}[/{status_style}]\n"
        f"[bold]Manufacturer:[/bold] {device.manufacturer or 'Unknown'}\n"
        f"[bold]Model:[/bold] {device.model_name or 'Unknown'}\n"
        f"[bold]Type:[/bold] {device.device_type or 'Unknown'}\n"
        f"[bold]Connected:[/bold] {'Yes' if device.connected else 'No'}\n"
        f"[bold]Guest:[/bold] {'Yes' if device.is_guest else 'No'}\n"
        f"[bold]Paused:[/bold] {'Yes' if device.paused else 'No'}\n"
        f"[bold]Blocked:[/bold] {'Yes' if device.blacklisted else 'No'}\n"
        f"[bold]Profile:[/bold] {profile_display}\n"
        f"[bold]Connection Type:[/bold] {device.connection_type or 'Unknown'}\n"
        f"[bold]Eero Location:[/bold] {device.source.location if device.source else 'Unknown'}\n",
        title=f"Device: {device_name}",
        border_style="blue",
    )
    console.print(panel)

    # Connectivity Information
    if device.connectivity:
        channel_width = "N/A"
        if device.connectivity.rx_rate_info and "channel_width" in device.connectivity.rx_rate_info:
            channel_width = device.connectivity.rx_rate_info["channel_width"]

        connectivity_panel = Panel(
            f"[bold]Signal:[/bold] {device.connectivity.signal or 'N/A'}\n"
            f"[bold]Score:[/bold] {device.connectivity.score or 'N/A'}\n"
            f"[bold]Score Bars:[/bold] {device.connectivity.score_bars or 'N/A'}\n"
            f"[bold]Frequency:[/bold] {device.connectivity.frequency or 'N/A'} MHz\n"
            f"[bold]RX Bitrate:[/bold] {device.connectivity.rx_bitrate or 'N/A'}\n"
            f"[bold]Channel Width:[/bold] {channel_width}\n",
            title="Connectivity",
            border_style="green",
        )
        console.print(connectivity_panel)

    # Interface Information
    if device.interface:
        interface_panel = Panel(
            f"[bold]Frequency:[/bold] {device.interface.frequency or 'N/A'} {device.interface.frequency_unit or ''}\n"
            f"[bold]Channel:[/bold] {device.channel or 'N/A'}\n"
            f"[bold]Authentication:[/bold] {device.auth or 'N/A'}\n",
            title="Interface",
            border_style="cyan",
        )
        console.print(interface_panel)


def create_blacklist_table(blacklist_data: List[Dict[str, Any]]) -> Table:
    """Create a table displaying blacklisted devices.

    Args:
        blacklist_data: List of blacklisted device dictionaries

    Returns:
        Rich Table object
    """
    table = Table(title="Blacklisted Devices")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Nickname", style="blue")
    table.add_column("IP", style="green")
    table.add_column("MAC", style="yellow")
    table.add_column("Type", style="cyan")
    table.add_column("Manufacturer", style="green")
    table.add_column("Connection Type", style="blue")
    table.add_column("Eero Location", style="yellow")
    table.add_column("Last Active", style="magenta")

    for device in blacklist_data:
        # Extract device ID from URL
        device_id = "Unknown"
        if device.get("url"):
            parts = device["url"].split("/")
            if len(parts) >= 2:
                device_id = parts[-1]

        # Use display_name, hostname, or nickname as the name
        device_name = (
            device.get("display_name")
            or device.get("hostname")
            or device.get("nickname")
            or "Unknown"
        )

        # Use primary IP address
        ip_address = device.get("ip") or "Unknown"

        # Use MAC address
        mac_address = device.get("mac") or "Unknown"

        # Connection type
        connection_type = device.get("connection_type") or "Unknown"

        # Eero source location
        source = device.get("source", {})
        eero_location = source.get("location") if source else "Unknown"

        # Last active time
        last_active = device.get("last_active") or "Unknown"

        table.add_row(
            device_id,
            device_name,
            device.get("nickname") or "",
            ip_address,
            mac_address,
            device.get("device_type") or "Unknown",
            device.get("manufacturer") or "Unknown",
            connection_type,
            eero_location,
            str(last_active),
        )

    return table
