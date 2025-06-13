"""Profiles API for Eero."""

import logging
from typing import Any, Dict, List, Optional

from ..const import ACCOUNT_ENDPOINT
from ..exceptions import EeroAuthenticationException
from .auth import AuthAPI
from .base import BaseAPI

_LOGGER = logging.getLogger(__name__)


class ProfilesAPI(BaseAPI):
    """Profiles API for Eero."""

    def __init__(self, auth_api: AuthAPI) -> None:
        """Initialize the ProfilesAPI.

        Args:
            auth_api: Authentication API instance
        """
        super().__init__(auth_api.session, None, ACCOUNT_ENDPOINT)
        self._auth_api = auth_api

    async def get_profiles(self, network_id: str) -> List[Dict[str, Any]]:
        """Get list of profiles.

        Args:
            network_id: ID of the network to get profiles from

        Returns:
            List of profile data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles",
            auth_token=auth_token,
        )
        return response.get("data", {}).get("data", [])

    async def get_profile(self, network_id: str, profile_id: str) -> Dict[str, Any]:
        """Get information about a specific profile.

        Args:
            network_id: ID of the network the profile belongs to
            profile_id: ID of the profile to get

        Returns:
            Profile data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        response = await self.get(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}",
            auth_token=auth_token,
        )
        return response.get("data", {})

    async def pause_profile(
        self, network_id: str, profile_id: str, paused: bool
    ) -> bool:
        """Pause or unpause internet access for a profile.

        Args:
            network_id: ID of the network the profile belongs to
            profile_id: ID of the profile
            paused: Whether to pause or unpause the profile

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
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}",
            auth_token=auth_token,
            json={"paused": paused},
        )
        return bool(response.get("meta", {}).get("code") == 200)

    async def update_profile_content_filter(
        self, network_id: str, profile_id: str, filters: Dict[str, bool]
    ) -> bool:
        """Update content filtering settings for a profile.

        Args:
            network_id: ID of the network the profile belongs to
            profile_id: ID of the profile
            filters: Dictionary of filter settings to update

        Returns:
            True if the operation was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        # Validate filter settings
        valid_filters = {
            "adblock",
            "adblock_plus",
            "safe_search",
            "block_malware",
            "block_illegal",
            "block_violent",
            "block_adult",
            "youtube_restricted",
        }

        content_filter = {}
        for key, value in filters.items():
            if key in valid_filters:
                content_filter[key] = value
            else:
                _LOGGER.warning(f"Ignoring invalid filter setting: {key}")

        response = await self.put(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}",
            auth_token=auth_token,
            json={"content_filter": content_filter},
        )
        return bool(response.get("meta", {}).get("code") == 200)

    async def update_profile_block_list(
        self,
        network_id: str,
        profile_id: str,
        domains: List[str],
        block: bool = True,
    ) -> bool:
        """Update custom domain block/allow list for a profile.

        Args:
            network_id: ID of the network the profile belongs to
            profile_id: ID of the profile
            domains: List of domains to block or allow
            block: True to add to block list, False for allow list

        Returns:
            True if the operation was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        auth_token = await self._auth_api.get_auth_token()
        if not auth_token:
            raise EeroAuthenticationException("Not authenticated")

        list_type = "custom_block_list" if block else "custom_allow_list"

        response = await self.put(
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}",
            auth_token=auth_token,
            json={list_type: domains},
        )
        return bool(response.get("meta", {}).get("code") == 200)
