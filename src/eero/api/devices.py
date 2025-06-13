"""Devices API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import ACCOUNT_ENDPOINT
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
        super().__init__(auth_api.session, None, ACCOUNT_ENDPOINT)
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

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices",
            auth_token=auth_token,
        )
        return response.get("data", {}).get("data", [])

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

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
            auth_token=auth_token,
        )
        return response.get("data", {})

    async def set_device_nickname(
        self, network_id: str, device_id: str, nickname: str
    ) -> bool:
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

        response = await self.put(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
            auth_token=auth_token,
            json={"nickname": nickname},
        )
        return bool(response.get("meta", {}).get("code") == 200)

    async def block_device(
        self, network_id: str, device_id: str, blocked: bool
    ) -> bool:
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

        response = await self.put(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
            auth_token=auth_token,
            json={"blocked": blocked},
        )
        return bool(response.get("meta", {}).get("code") == 200)
