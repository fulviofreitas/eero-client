"""Device-related models for the Eero API."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from ..const import EeroDeviceStatus


class DeviceTag(BaseModel):
    """Model representing a device tag."""

    id: str = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    color: Optional[str] = Field(None, description="Tag color")


class DeviceConnection(BaseModel):
    """Model representing a device connection."""

    type: str = Field(..., description="Connection type (wired/wireless)")
    connected_to: Optional[str] = Field(None, description="Connected to device ID")
    connected_via: Optional[str] = Field(
        None, description="Connected via (e.g., 'wifi', 'ethernet')"
    )
    frequency: Optional[str] = Field(None, description="Frequency (2.4GHz/5GHz)")
    signal_strength: Optional[int] = Field(None, description="Signal strength")
    tx_rate: Optional[int] = Field(None, description="TX rate")
    rx_rate: Optional[int] = Field(None, description="RX rate")


class Device(BaseModel):
    """Model representing a device connected to an Eero network."""

    id: str = Field(..., description="Unique identifier for the device")
    name: str = Field(..., description="Device name")
    nickname: Optional[str] = Field(None, description="User-defined device nickname")
    network_id: str = Field(..., description="Network ID this device belongs to")
    mac_address: str = Field(..., description="MAC address")
    ip_address: Optional[str] = Field(None, description="IP address")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    model: Optional[str] = Field(None, description="Model name")
    connected: bool = Field(False, description="Whether the device is connected")
    wireless: bool = Field(False, description="Whether the device is wireless")
    connection: Optional[DeviceConnection] = Field(
        None, description="Connection details"
    )
    status: EeroDeviceStatus = Field(
        EeroDeviceStatus.UNKNOWN, description="Device status"
    )
    first_seen: Optional[datetime] = Field(None, description="When first seen")
    last_seen: Optional[datetime] = Field(None, description="When last seen")
    paused: bool = Field(False, description="Whether internet access is paused")
    blocked: bool = Field(False, description="Whether device is blocked")
    guest: bool = Field(False, description="Whether device is on guest network")
    profile_id: Optional[str] = Field(None, description="Associated profile ID")
    tags: List[DeviceTag] = Field(default_factory=list, description="Device tags")
    hostname: Optional[str] = Field(None, description="Device hostname")
    device_type: Optional[str] = Field(None, description="Device type")
    usage: Optional[Dict[str, Any]] = Field(None, description="Usage statistics")
    
    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
