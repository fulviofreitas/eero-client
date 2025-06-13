"""Eero device-specific models for the Eero API."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from ..const import EeroDeviceType


class Location(BaseModel):
    """Model representing the location of an Eero device."""

    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")
    address: Optional[str] = Field(None, description="Address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    zip_code: Optional[str] = Field(None, description="Postal/ZIP code")


class EeroHealth(BaseModel):
    """Model representing the health status of an Eero device."""

    status: str = Field(..., description="Health status")
    issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="Health issues"
    )


class Eero(BaseModel):
    """Model representing an Eero device."""

    id: str = Field(..., description="Unique identifier for the Eero")
    name: str = Field(..., description="Eero name")
    network_id: str = Field(..., description="Network ID this Eero belongs to")
    mac_address: str = Field(..., description="MAC address")
    model: str = Field(..., description="Model name")
    serial: str = Field(..., description="Serial number")
    device_type: EeroDeviceType = Field(
        EeroDeviceType.UNKNOWN, description="Eero device type"
    )
    created_at: datetime = Field(..., description="When the Eero was created")
    updated_at: datetime = Field(..., description="When the Eero was last updated")
    firmware_version: str = Field(..., description="Firmware version")
    ip_address: Optional[str] = Field(None, description="IP address")
    status: str = Field(..., description="Current status")
    connected: bool = Field(False, description="Whether the Eero is connected")
    is_gateway: bool = Field(False, description="Whether the Eero is a gateway")
    is_primary: bool = Field(False, description="Whether the Eero is primary")
    backup_connection: bool = Field(
        False, description="Whether using backup connection"
    )
    wired: bool = Field(False, description="Whether the Eero is wired")
    connected_clients_count: int = Field(
        0, description="Number of connected clients"
    )
    health: Optional[EeroHealth] = Field(None, description="Health status")
    location: Optional[Location] = Field(None, description="Physical location")
    parent: Optional[str] = Field(None, description="Parent Eero ID")
    last_heartbeat: Optional[datetime] = Field(
        None, description="Last heartbeat timestamp"
    )
    uptime: Optional[int] = Field(None, description="Uptime in seconds")
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    
    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
