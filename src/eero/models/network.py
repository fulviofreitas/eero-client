"""Network-related models for the Eero API."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from ..const import EeroNetworkStatus


class NetworkSettings(BaseModel):
    """Model representing network settings."""

    ipv6_upstream: bool = Field(False, description="IPv6 upstream enabled")
    band_steering: bool = Field(False, description="Band steering enabled")
    thread_enabled: bool = Field(False, description="Thread enabled")
    upnp_enabled: bool = Field(False, description="UPnP enabled")
    wpa3_transition: bool = Field(False, description="WPA3 transition mode enabled")
    dns_caching: bool = Field(True, description="DNS caching enabled")
    ipv6_downstream: bool = Field(False, description="IPv6 downstream enabled")
    target_firmware: Optional[str] = Field(None, description="Target firmware version")
    gateway_mac_address: Optional[str] = Field(None, description="Gateway MAC address")


class DHCP(BaseModel):
    """Model representing DHCP configuration."""

    lease_time_seconds: int = Field(..., description="DHCP lease time in seconds")
    dns_server: Optional[str] = Field(None, description="DNS server")
    subnet_mask: str = Field(..., description="Subnet mask")
    starting_address: str = Field(..., description="Starting IP address")
    ending_address: str = Field(..., description="Ending IP address")


class Network(BaseModel):
    """Model representing an Eero network."""

    id: str = Field(..., description="Unique identifier for the network")
    name: str = Field(..., description="Network name")
    status: EeroNetworkStatus = Field(
        EeroNetworkStatus.UNKNOWN, description="Network status"
    )
    created_at: datetime = Field(..., description="When the network was created")
    updated_at: datetime = Field(..., description="When the network was last updated")
    speed_test: Optional[Dict[str, Any]] = Field(
        None, description="Latest speed test results"
    )
    bandwidth_limits: Optional[Dict[str, Any]] = Field(
        None, description="Bandwidth limits configuration"
    )
    health: Optional[Dict[str, Any]] = Field(None, description="Network health status")
    dhcp: Optional[DHCP] = Field(None, description="DHCP configuration")
    settings: NetworkSettings = Field(
        default_factory=NetworkSettings, description="Network settings"
    )
    guest_network_enabled: bool = Field(
        False, description="Guest network enabled status"
    )
    guest_network_name: Optional[str] = Field(None, description="Guest network name")
    guest_network_password: Optional[str] = Field(
        None, description="Guest network password"
    )
    isp_name: Optional[str] = Field(None, description="ISP name")
    public_ip: Optional[str] = Field(None, description="Public IP address")
    
    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
