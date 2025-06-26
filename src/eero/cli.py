"""High-level client for interacting with Eero networks."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Union, cast

import aiohttp
from aiohttp import ClientSession

from .api import EeroAPI
from .exceptions import EeroAuthenticationException, EeroException
from .models.account import Account
from .models.device import Device
from .models.eero import Eero
from .models.network import Network
from .models.profile import Profile

_LOGGER = logging.getLogger(__name__)


class EeroClient:
    """High-level client for interacting with Eero networks."""

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        cookie_file: Optional[str] = None,
        use_keyring: bool = True,
        cache_timeout: int = 60,
    ) -> None:
        """Initialize the EeroClient.

        Args:
            session: Optional aiohttp ClientSession to use for requests
            cookie_file: Optional path to a file for storing authentication cookies
            use_keyring: Whether to use keyring for secure token storage
            cache_timeout: Cache timeout in seconds
        """
        self._api = EeroAPI(session=session, cookie_file=cookie_file, use_keyring=use_keyring)
        self._cache_timeout = cache_timeout
        self._cache: Dict[str, Dict] = {
            "account": {"data": None, "timestamp": 0},
            "networks": {"data": None, "timestamp": 0},
            "network": {},
            "eeros": {},
            "devices": {},
            "profiles": {},
        }

    async def __aenter__(self) -> "EeroClient":
        """Enter async context manager."""
        await self._api.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self._api.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self._api.is_authenticated

    def _is_cache_valid(self, cache_key: str, subkey: Optional[str] = None) -> bool:
        """Check if a cache entry is valid.

        Args:
            cache_key: Main cache key
            subkey: Optional subkey

        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self._cache:
            return False

        if subkey is None:
            cache_entry = self._cache[cache_key]
        else:
            if subkey not in self._cache[cache_key]:
                return False
            cache_entry = self._cache[cache_key][subkey]

        if not cache_entry or "timestamp" not in cache_entry:
            return False

        current_time = asyncio.get_event_loop().time()
        return (current_time - cache_entry["timestamp"]) < self._cache_timeout

    def _update_cache(self, cache_key: str, subkey: Optional[str], data: any) -> None:
        """Update a cache entry.

        Args:
            cache_key: Main cache key
            subkey: Optional subkey
            data: Data to cache
        """
        current_time = asyncio.get_event_loop().time()

        if subkey is None:
            self._cache[cache_key] = {"data": data, "timestamp": current_time}
        else:
            if cache_key not in self._cache:
                self._cache[cache_key] = {}
            self._cache[cache_key][subkey] = {"data": data, "timestamp": current_time}

    def _get_from_cache(self, cache_key: str, subkey: Optional[str] = None) -> any:
        """Get data from cache.

        Args:
            cache_key: Main cache key
            subkey: Optional subkey

        Returns:
            Cached data or None if not in cache
        """
        if cache_key not in self._cache:
            return None

        if subkey is None:
            cache_entry = self._cache[cache_key]
        else:
            if subkey not in self._cache[cache_key]:
                return None
            cache_entry = self._cache[cache_key][subkey]

        return cache_entry.get("data")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        for cache_key in self._cache:
            if isinstance(self._cache[cache_key], dict) and "data" in self._cache[cache_key]:
                self._cache[cache_key]["data"] = None
            else:
                self._cache[cache_key] = {}

    async def login(self, user_identifier: str) -> bool:
        """Start the login process by requesting a verification code.

        Args:
            user_identifier: Email address or phone number for the Eero account

        Returns:
            True if login request was successful
        """
        return await self._api.login(user_identifier)

    async def verify(self, verification_code: str) -> bool:
        """Verify login with the code sent to the user.

        Args:
            verification_code: The verification code sent to the user

        Returns:
            True if verification was successful
        """
        result = await self._api.verify(verification_code)
        if result:
            # Clear cache on successful login
            self.clear_cache()
        return result

    async def logout(self) -> bool:
        """Log out from the Eero API.

        Returns:
            True if logout was successful
        """
        result = await self._api.logout()
        if result:
            # Clear cache on successful logout
            self.clear_cache()
        return result

    async def get_account(self, refresh_cache: bool = False) -> Account:
        """Get account information.

        Args:
            refresh_cache: Whether to refresh the cache

        Returns:
            Account object
        """
        if not refresh_cache and self._is_cache_valid("account"):
            account_data = self._get_from_cache("account")
            if account_data:
                return Account.model_validate(account_data)

        account_data = await self._api.auth.get(
            "/account", auth_token=await self._api.auth.get_auth_token()
        )
        account_data = account_data.get("data", {})
        self._update_cache("account", None, account_data)

        return Account.model_validate(account_data)

    async def get_networks(self, refresh_cache: bool = False) -> List[Network]:
        """Get list of networks.

        Args:
            refresh_cache: Whether to refresh the cache

        Returns:
            List of Network objects
        """
        if not refresh_cache and self._is_cache_valid("networks"):
            networks_data = self._get_from_cache("networks")
            if networks_data:
                return [Network.model_validate(net) for net in networks_data]

        networks_data = await self._api.networks.get_networks()
        self._update_cache("networks", None, networks_data)

        # Set preferred network ID if not already set and we have networks
        if not self._api.preferred_network_id and networks_data:
            # Try to get ID directly from the network
            network_id = networks_data[0].get("id")
            if network_id:
                self._api.set_preferred_network(network_id)
            else:
                # Try to extract from URL
                network_url = networks_data[0].get("url")
                if network_url:
                    # URL format is usually "/2.2/networks/network_id"
                    parts = network_url.split("/")
                    if len(parts) > 0:
                        network_id = parts[-1]
                        self._api.set_preferred_network(network_id)

        # If we still have no networks but do have a preferred network ID,
        # construct a minimal network object
        if not networks_data and self._api.preferred_network_id:
            network_id = self._api.preferred_network_id
            _LOGGER.debug(f"No networks found but using preferred network ID: {network_id}")

            # Try to get network details
            try:
                network_details = await self._api.networks.get_network(network_id)
                if network_details:
                    networks_data = [network_details]
                    self._update_cache("networks", None, networks_data)
            except Exception as e:
                _LOGGER.warning(f"Failed to get details for preferred network: {e}")
                # Create a minimal network entry
                networks_data = [
                    {
                        "id": network_id,
                        "url": f"/2.2/networks/{network_id}",
                        "name": "Eero Network",
                        "status": "unknown",
                    }
                ]
                self._update_cache("networks", None, networks_data)

        return [Network.model_validate(net) for net in networks_data]

    async def get_network(
        self, network_id: Optional[str] = None, refresh_cache: bool = False
    ) -> Network:
        """Get network information.

        Args:
            network_id: ID of the network to get (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            Network object

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        if not refresh_cache and self._is_cache_valid("network", network_id):
            network_data = self._get_from_cache("network", network_id)
            if network_data:
                return Network.model_validate(network_data)

        try:
            network_data = await self._api.networks.get_network(network_id)
            self._update_cache("network", network_id, network_data)
            return Network.model_validate(network_data)
        except Exception as e:
            _LOGGER.warning(f"Error getting network details: {e}")
            # Create a minimal network object
            network_data = {
                "id": network_id,
                "url": f"/2.2/networks/{network_id}",
                "name": "Eero Network",
                "status": "unknown",
            }
            self._update_cache("network", network_id, network_data)
            return Network.model_validate(network_data)

    async def get_eeros(
        self, network_id: Optional[str] = None, refresh_cache: bool = False
    ) -> List[Eero]:
        """Get list of Eero devices.

        Args:
            network_id: ID of the network to get Eeros from (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            List of Eero objects

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        cache_key = f"{network_id}_eeros"
        if not refresh_cache and self._is_cache_valid("eeros", cache_key):
            eeros_data = self._get_from_cache("eeros", cache_key)
            if eeros_data:
                return [Eero.model_validate(eero) for eero in eeros_data]

        eeros_data = await self._api.eeros.get_eeros(network_id)
        self._update_cache("eeros", cache_key, eeros_data)
        return [Eero.model_validate(eero) for eero in eeros_data]

    async def get_eero(
        self,
        eero_id: str,
        network_id: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> Eero:
        """Get information about a specific Eero device.

        Args:
            eero_id: ID of the Eero device to get
            network_id: ID of the network the Eero belongs to (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            Eero object

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        cache_key = f"{network_id}_{eero_id}"
        if not refresh_cache and self._is_cache_valid("eeros", cache_key):
            eero_data = self._get_from_cache("eeros", cache_key)
            if eero_data:
                return Eero.model_validate(eero_data)

        eero_data = await self._api.eeros.get_eero(network_id, eero_id)
        self._update_cache("eeros", cache_key, eero_data)
        return Eero.model_validate(eero_data)

    async def get_devices(
        self, network_id: Optional[str] = None, refresh_cache: bool = False
    ) -> List[Device]:
        """Get list of connected devices.

        Args:
            network_id: ID of the network to get devices from (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            List of Device objects

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        cache_key = f"{network_id}_devices"
        if not refresh_cache and self._is_cache_valid("devices", cache_key):
            devices_data = self._get_from_cache("devices", cache_key)
            if devices_data:
                return [Device.model_validate(device) for device in devices_data]

        devices_data = await self._api.devices.get_devices(network_id)
        self._update_cache("devices", cache_key, devices_data)
        return [Device.model_validate(device) for device in devices_data]

    async def get_device(
        self,
        device_id: str,
        network_id: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> Device:
        """Get information about a specific device.

        Args:
            device_id: ID of the device to get
            network_id: ID of the network the device belongs to (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            Device object

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        cache_key = f"{network_id}_{device_id}"
        if not refresh_cache and self._is_cache_valid("devices", cache_key):
            device_data = self._get_from_cache("devices", cache_key)
            if device_data:
                return Device.model_validate(device_data)

        device_data = await self._api.devices.get_device(network_id, device_id)
        self._update_cache("devices", cache_key, device_data)
        return Device.model_validate(device_data)

    async def get_profiles(
        self, network_id: Optional[str] = None, refresh_cache: bool = False
    ) -> List[Profile]:
        """Get list of profiles.

        Args:
            network_id: ID of the network to get profiles from (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            List of Profile objects

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        cache_key = f"{network_id}_profiles"
        if not refresh_cache and self._is_cache_valid("profiles", cache_key):
            profiles_data = self._get_from_cache("profiles", cache_key)
            if profiles_data:
                return [Profile.model_validate(profile) for profile in profiles_data]

        profiles_data = await self._api.profiles.get_profiles(network_id)
        self._update_cache("profiles", cache_key, profiles_data)
        return [Profile.model_validate(profile) for profile in profiles_data]

    async def get_profile(
        self,
        profile_id: str,
        network_id: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> Profile:
        """Get information about a specific profile.

        Args:
            profile_id: ID of the profile to get
            network_id: ID of the network the profile belongs to (uses preferred network if None)
            refresh_cache: Whether to refresh the cache

        Returns:
            Profile object

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        cache_key = f"{network_id}_{profile_id}"
        if not refresh_cache and self._is_cache_valid("profiles", cache_key):
            profile_data = self._get_from_cache("profiles", cache_key)
            if profile_data:
                return Profile.model_validate(profile_data)

        profile_data = await self._api.profiles.get_profile(network_id, profile_id)
        self._update_cache("profiles", cache_key, profile_data)
        return Profile.model_validate(profile_data)

    async def reboot_eero(self, eero_id: str, network_id: Optional[str] = None) -> bool:
        """Reboot an Eero device.

        Args:
            eero_id: ID of the Eero device to reboot
            network_id: ID of the network the Eero belongs to (uses preferred network if None)

        Returns:
            True if reboot was successful

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        result = await self._api.eeros.reboot_eero(network_id, eero_id)

        # Clear cache for this eero
        if result:
            cache_key = f"{network_id}_{eero_id}"
            if cache_key in self._cache.get("eeros", {}):
                del self._cache["eeros"][cache_key]

        return result

    async def set_guest_network(
        self,
        enabled: bool,
        name: Optional[str] = None,
        password: Optional[str] = None,
        network_id: Optional[str] = None,
    ) -> bool:
        """Enable or disable the guest network.

        Args:
            enabled: Whether to enable or disable the guest network
            name: Optional new name for the guest network
            password: Optional new password for the guest network
            network_id: ID of the network (uses preferred network if None)

        Returns:
            True if the operation was successful

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        result = await self._api.networks.set_guest_network(network_id, enabled, name, password)

        # Clear network cache on success
        if result and network_id in self._cache.get("network", {}):
            del self._cache["network"][network_id]

        return result

    async def set_device_nickname(
        self, device_id: str, nickname: str, network_id: Optional[str] = None
    ) -> bool:
        """Set a nickname for a device.

        Args:
            device_id: ID of the device
            nickname: New nickname for the device
            network_id: ID of the network the device belongs to (uses preferred network if None)

        Returns:
            True if the operation was successful

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        result = await self._api.devices.set_device_nickname(network_id, device_id, nickname)

        # Clear device cache on success
        if result:
            cache_key = f"{network_id}_{device_id}"
            if cache_key in self._cache.get("devices", {}):
                del self._cache["devices"][cache_key]

            # Also clear devices list cache
            cache_key = f"{network_id}_devices"
            if cache_key in self._cache.get("devices", {}):
                del self._cache["devices"][cache_key]

        return result

    async def block_device(
        self, device_id: str, blocked: bool, network_id: Optional[str] = None
    ) -> bool:
        """Block or unblock a device.

        Args:
            device_id: ID of the device
            blocked: Whether to block or unblock the device
            network_id: ID of the network the device belongs to (uses preferred network if None)

        Returns:
            True if the operation was successful

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        result = await self._api.devices.block_device(network_id, device_id, blocked)

        # Clear device cache on success
        if result:
            cache_key = f"{network_id}_{device_id}"
            if cache_key in self._cache.get("devices", {}):
                del self._cache["devices"][cache_key]

            # Also clear devices list cache
            cache_key = f"{network_id}_devices"
            if cache_key in self._cache.get("devices", {}):
                del self._cache["devices"][cache_key]

        return result

    async def pause_profile(
        self, profile_id: str, paused: bool, network_id: Optional[str] = None
    ) -> bool:
        """Pause or unpause internet access for a profile.

        Args:
            profile_id: ID of the profile
            paused: Whether to pause or unpause the profile
            network_id: ID of the network the profile belongs to (uses preferred network if None)

        Returns:
            True if the operation was successful

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        result = await self._api.profiles.pause_profile(network_id, profile_id, paused)

        # Clear profile cache on success
        if result:
            cache_key = f"{network_id}_{profile_id}"
            if cache_key in self._cache.get("profiles", {}):
                del self._cache["profiles"][cache_key]

            # Also clear profiles list cache
            cache_key = f"{network_id}_profiles"
            if cache_key in self._cache.get("profiles", {}):
                del self._cache["profiles"][cache_key]

        return result

    async def run_speed_test(self, network_id: Optional[str] = None) -> Dict:
        """Run a speed test on the network.

        Args:
            network_id: ID of the network to run the speed test on (uses preferred network if None)

        Returns:
            Speed test results

        Raises:
            EeroException: If no network ID is available
        """
        network_id = network_id or self._api.preferred_network_id
        if not network_id:
            # Try to get networks to set preferred network
            networks = await self.get_networks()
            if networks:
                network_id = networks[0].id
            else:
                raise EeroException("No network ID available")

        result = await self._api.networks.run_speed_test(network_id)

        # Clear network cache
        if network_id in self._cache.get("network", {}):
            del self._cache["network"][network_id]

        return result

    def set_preferred_network(self, network_id: str) -> None:
        """Set the preferred network ID to use for requests.

        Args:
            network_id: ID of the network to use
        """
        self._api.set_preferred_network(network_id)
