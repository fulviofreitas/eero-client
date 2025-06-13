"""Networks API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import ACCOUNT_ENDPOINT
from ..exceptions import EeroAuthenticationException
from .auth import AuthAPI
from .base import BaseAPI

_LOGGER = logging.getLogger(__name__)


class NetworksAPI(BaseAPI):
    """Networks API for Eero."""

    def __init__(self, auth_api: AuthAPI) -> None:
        """Initialize the NetworksAPI.

        Args:
            auth_api: Authentication API instance
        """
        super().__init__(auth_api.session, None, ACCOUNT_ENDPOINT)
        self._auth_api = auth_api

    async def get_networks(self) -> List[Dict[str, Any]]:
        """Get list of networks.

        Returns:
            List of network data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks",
            auth_token=auth_token,
        )
        return response.get("data", {}).get("data", [])

    async def get_network(self, network_id: str) -> Dict[str, Any]:
        """Get network information.

        Args:
            network_id: ID of the network to get

        Returns:
            Network data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}",
            auth_token=auth_token,
        )
        return response.get("data", {})

    async def set_guest_network(
        self,
        network_id: str,
        enabled: bool,
        name: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """Enable or disable the guest network.

        Args:
            network_id: ID of the network
            enabled: Whether to enable or disable the guest network
            name: Optional new name for the guest network
            password: Optional new password for the guest network

        Returns:
            True if the operation was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        payload: Dict[str, Any] = {"enabled": enabled}

        if name is not None:
            payload["name"] = name

        if password is not None:
            payload["password"] = password

        response = await self.put(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/guest_network",
            auth_token=auth_token,
            json=payload,
        )
        return bool(response.get("meta", {}).get("code") == 200)

    async def run_speed_test(self, network_id: str) -> Dict[str, Any]:
        """Run a speed test on the network.

        Args:
            network_id: ID of the network to run the speed test on

        Returns:
            Speed test results

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        response = await self.post(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/speedtest",
            auth_token=auth_token,
            json={},
        )
        return response.get("data", {})
