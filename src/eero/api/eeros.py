"""Eero devices API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import API_ENDPOINT
from ..exceptions import EeroAuthenticationException
from .auth import AuthAPI
from .base import BaseAPI

_LOGGER = logging.getLogger(__name__)


class EerosAPI(BaseAPI):
    """Eero devices API for Eero."""

    def __init__(self, auth_api: AuthAPI) -> None:
        """Initialize the EerosAPI.

        Args:
            auth_api: Authentication API instance
        """
        # Use API_ENDPOINT as the base URL, not ACCOUNT_ENDPOINT
        super().__init__(auth_api.session, None, API_ENDPOINT)
        self._auth_api = auth_api

    async def get_eeros(self, network_id: str) -> List[Dict[str, Any]]:
        """Get list of Eero devices.

        Args:
            network_id: ID of the network to get Eeros from

        Returns:
            List of Eero device data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Getting eeros for network {network_id}")

        # Simplified path construction
        response = await self.get(
            f"networks/{network_id}/eeros",
            auth_token=auth_token,
        )

        # Handle different response formats
        data = response.get("data", [])
        if isinstance(data, list):
            # Data is directly a list of eeros
            eeros_data = data
        elif isinstance(data, dict) and "data" in data:
            # Data is a dictionary with a nested data field
            eeros_data = data.get("data", [])
        else:
            # Fallback to empty list
            eeros_data = []

        _LOGGER.debug(f"Found {len(eeros_data)} eeros")

        return eeros_data

    async def get_eero(self, network_id: str, eero_id: str) -> Dict[str, Any]:
        """Get information about a specific Eero device.

        Args:
            network_id: ID of the network the Eero belongs to
            eero_id: ID of the Eero device to get

        Returns:
            Eero device data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Getting eero {eero_id} in network {network_id}")

        # Simplified path construction
        response = await self.get(
            f"networks/{network_id}/eeros/{eero_id}",
            auth_token=auth_token,
        )

        return response.get("data", {})

    async def reboot_eero(self, network_id: str, eero_id: str) -> bool:
        """Reboot an Eero device.

        Args:
            network_id: ID of the network the Eero belongs to
            eero_id: ID of the Eero device to reboot

        Returns:
            True if reboot was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Rebooting eero {eero_id} in network {network_id}")

        # Simplified path construction
        response = await self.post(
            f"networks/{network_id}/eeros/{eero_id}/reboot",
            auth_token=auth_token,
            json={},
        )

        return bool(response.get("meta", {}).get("code") == 200)
