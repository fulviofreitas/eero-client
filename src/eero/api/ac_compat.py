"""AC Compatibility API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import API_ENDPOINT
from ..exceptions import EeroAuthenticationException
from .auth import AuthAPI
from .base import BaseAPI

_LOGGER = logging.getLogger(__name__)


class ACCompatAPI(BaseAPI):
    """AC Compatibility API for Eero."""

    def __init__(self, auth_api: AuthAPI) -> None:
        """Initialize the ACCompatAPI.

        Args:
            auth_api: Authentication API instance
        """
        super().__init__(auth_api.session, None, API_ENDPOINT)
        self._auth_api = auth_api

    async def get_ac_compat(self, network_id: str) -> Dict[str, Any]:
        """Get AC compatibility information.

        Args:
            network_id: ID of the network to get AC compatibility info for

        Returns:
            AC compatibility data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        _LOGGER.debug(f"Getting AC compatibility for network {network_id}")

        response = await self.get(
            f"networks/{network_id}/ac_compat",
            auth_token=auth_token,
        )

        return response.get("data", {})
