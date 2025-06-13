"""Eero devices API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import ACCOUNT_ENDPOINT
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
        super().__init__(auth_api.session, None, ACCOUNT_ENDPOINT)
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

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros",
            auth_token=auth_token,
        )
        return response.get("data", {}).get("data", [])

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

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros/{eero_id}",
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

        response = await self.post(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros/{eero_id}/reboot",
            auth_token=auth_token,
            json={},
        )
        return bool(response.get("meta", {}).get("code") == 200)
