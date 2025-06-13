"""Profile-related models for the Eero API."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class ProfileScheduleBlock(BaseModel):
    """Model representing a time block in a profile schedule."""

    days: List[str] = Field(..., description="Days of the week")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")


class ContentFilter(BaseModel):
    """Model representing content filtering settings."""

    adblock: bool = Field(False, description="Ad blocking enabled")
    adblock_plus: bool = Field(False, description="Enhanced ad blocking enabled")
    safe_search: bool = Field(False, description="Safe search enabled")
    block_malware: bool = Field(False, description="Malware blocking enabled")
    block_illegal: bool = Field(False, description="Illegal content blocking enabled")
    block_violent: bool = Field(False, description="Violent content blocking enabled")
    block_adult: bool = Field(False, description="Adult content blocking enabled")
    youtube_restricted: bool = Field(
        False, description="YouTube restricted mode enabled"
    )


class Profile(BaseModel):
    """Model representing a profile for grouped devices."""

    id: str = Field(..., description="Unique identifier for the profile")
    name: str = Field(..., description="Profile name")
    network_id: str = Field(..., description="Network ID this profile belongs to")
    device_count: int = Field(0, description="Number of devices in this profile")
    connected_device_count: int = Field(
        0, description="Number of connected devices in this profile"
    )
    paused: bool = Field(False, description="Whether internet access is paused")
    premium_enabled: bool = Field(
        False, description="Whether premium features are enabled"
    )
    schedule_enabled: bool = Field(False, description="Whether schedule is enabled")
    schedule_blocks: List[ProfileScheduleBlock] = Field(
        default_factory=list, description="Schedule blocks"
    )
    content_filter: Optional[ContentFilter] = Field(
        None, description="Content filtering settings"
    )
    device_ids: List[str] = Field(default_factory=list, description="Device IDs")
    custom_block_list: List[str] = Field(
        default_factory=list, description="Custom blocked domains"
    )
    custom_allow_list: List[str] = Field(
        default_factory=list, description="Custom allowed domains"
    )
    usage: Optional[Dict[str, Any]] = Field(None, description="Usage statistics")
    
    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
