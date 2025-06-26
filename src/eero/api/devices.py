"""Devices API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import API_ENDPOINT
from ..exceptions import EeroAuthenticationException
from .auth import AuthAPI
from .base import BaseAPI

_LOGGER = logging.getLogger(__name__)


class DevicesAPI(BaseAPI):
    """Devices API for Eero."""

    def __init__(self, auth_api: AuthAPI) -> None:
        """Initialize the DevicesAPI.

        Args:
            auth_api: Authentication API instance
        """
        # Use API_ENDPOINT as the base URL, not ACCOUNT_ENDPOINT
        super().__init__(auth_api.session, None, API_ENDPOINT)
        self._auth_api = auth_api

    async def get_devices(self, network_id: str) -> List[Dict[str, Any]]:
        """Get list of connected devices.

        Args:
            network_id: ID of the network to get devices from

        Returns:
            List of device data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Getting devices for network {network_id}")

        # Simplified path construction
        response = await self.get(
            f"networks/{network_id}/devices",
            auth_token=auth_token,
        )

        # Handle different response formats
        data = response.get("data", [])
        if isinstance(data, list):
            # Data is directly a list of devices
            devices_data = data
        elif isinstance(data, dict) and "data" in data:
            # Data is a dictionary with a nested data field
            devices_data = data.get("data", [])
        else:
            # Fallback to empty list
            devices_data = []

        _LOGGER.debug(f"Found {len(devices_data)} devices")

        return devices_data

    async def get_device(self, network_id: str, device_id: str) -> Dict[str, Any]:
        """Get information about a specific device.

        Args:
            network_id: ID of the network the device belongs to
            device_id: ID of the device to get

        Returns:
            Device data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Getting device {device_id} in network {network_id}")

        # Simplified path construction
        response = await self.get(
            f"networks/{network_id}/devices/{device_id}",
            auth_token=auth_token,
        )

        return response.get("data", {})

    async def set_device_nickname(self, network_id: str, device_id: str, nickname: str) -> bool:
        """Set a nickname for a device.

        Args:
            network_id: ID of the network the device belongs to
            device_id: ID of the device
            nickname: New nickname for the device

        Returns:
            True if the operation was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Setting nickname for device {device_id} to '{nickname}'")

        # Simplified path construction
        response = await self.put(
            f"networks/{network_id}/devices/{device_id}",
            auth_token=auth_token,
            json={"nickname": nickname},
        )

        return bool(response.get("meta", {}).get("code") == 200)

    async def block_device(self, network_id: str, device_id: str, blocked: bool) -> bool:
        """Block or unblock a device.

        Args:
            network_id: ID of the network the device belongs to
            device_id: ID of the device
            blocked: Whether to block or unblock the device

        Returns:
            True if the operation was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"{'Blocking' if blocked else 'Unblocking'} device {device_id}")

        # Simplified path construction
        response = await self.put(
            f"networks/{network_id}/devices/{device_id}",
            auth_token=auth_token,
            json={"blocked": blocked},
        )

        return bool(response.get("meta", {}).get("code") == 200)
