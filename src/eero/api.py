"""API client for interacting with the Eero API."""

import asyncio
import json
import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import aiohttp

from .const import (
    ACCOUNT_ENDPOINT,
    DEFAULT_HEADERS,
    LOGIN_ENDPOINT,
    LOGIN_VERIFY_ENDPOINT,
    LOGOUT_ENDPOINT,
    SESSION_TOKEN_KEY,
)
from .exceptions import (
    EeroAPIException,
    EeroAuthenticationException,
    EeroNetworkException,
    EeroRateLimitException,
    EeroTimeoutException,
)

_LOGGER = logging.getLogger(__name__)


class EeroAPI:
    """API client for interacting with the Eero API."""

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        cookie_file: Optional[str] = None,
    ) -> None:
        """Initialize the EeroAPI.

        Args:
            session: Optional aiohttp ClientSession to use for requests
            cookie_file: Optional path to a file for storing authentication cookies
        """
        self._session = session
        self._cookie_file = cookie_file
        self._user_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._session_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._preferred_network_id: Optional[str] = None
        self._session_expiry: Optional[datetime] = None
        self._headers = DEFAULT_HEADERS.copy()
        self._should_close_session = False

    async def __aenter__(self) -> "EeroAPI":
        """Enter async context manager."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._should_close_session = True
        if self._cookie_file:
            await self._load_cookies()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self._should_close_session and self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the active aiohttp session or create a new one."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._should_close_session = True
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return bool(self._user_token and self._session_id)

    async def _load_cookies(self) -> None:
        """Load authentication cookies from file."""
        if not self._cookie_file:
            return

        try:
            with open(self._cookie_file, "r") as f:
                cookies = json.load(f)
                self._user_token = cookies.get("user_token")
                self._refresh_token = cookies.get("refresh_token")
                self._session_id = cookies.get("session_id")
                self._user_id = cookies.get("user_id")
                self._preferred_network_id = cookies.get("preferred_network_id")

                expiry = cookies.get("session_expiry")
                if expiry:
                    self._session_expiry = datetime.fromisoformat(expiry)

                # If session is expired, clear tokens
                if self._session_expiry and self._session_expiry < datetime.now():
                    self._user_token = None
                    self._session_id = None
                elif self._session_id:
                    # Set the cookie in aiohttp format
                    self._session.cookie_jar.update_cookies({"s": self._session_id})
                    _LOGGER.debug(f"Loaded cookie: s={self._session_id}")
        except (FileNotFoundError, json.JSONDecodeError):
            _LOGGER.debug("No valid cookie file found at %s", self._cookie_file)

    async def _save_cookies(self) -> None:
        """Save authentication cookies to file."""
        if not self._cookie_file:
            return

        cookies = {
            "user_token": self._user_token,
            "refresh_token": self._refresh_token,
            "session_id": self._session_id,
            "user_id": self._user_id,
            "preferred_network_id": self._preferred_network_id,
            "session_expiry": (
                self._session_expiry.isoformat() if self._session_expiry else None
            ),
        }

        with open(self._cookie_file, "w") as f:
            json.dump(cookies, f)

    async def login(self, user_identifier: str) -> bool:
        """Start the login process by requesting a verification code.

        Args:
            user_identifier: Email address or phone number for the Eero account

        Returns:
            True if login request was successful

        Raises:
            EeroAuthenticationException: If login fails
            EeroNetworkException: If there's a network error
        """
        if self.is_authenticated:
            return True

        try:
            async with self.session.post(
                LOGIN_ENDPOINT,
                headers=self._headers,
                json={"login": user_identifier},
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(
                    f"Login response status: {response.status}, body: {response_text}"
                )

                if response.status == 200:
                    data = await response.json()
                    # Extract user_token from the nested structure
                    self._user_token = data.get("data", {}).get("user_token")
                    _LOGGER.debug(f"Extracted user_token: {self._user_token}")
                    return bool(self._user_token)
                else:
                    response_text = await response.text()
                    _LOGGER.error(
                        "Login failed with status %s: %s",
                        response.status,
                        response_text,
                    )
                    raise EeroAuthenticationException(
                        f"Login failed: {response.status} - {response_text}"
                    )
        except aiohttp.ClientError as err:
            raise EeroNetworkException(f"Network error during login: {err}") from err

    async def verify(self, verification_code: str) -> bool:
        """Verify login with the code sent to the user.

        Args:
            verification_code: The verification code sent to the user

        Returns:
            True if verification was successful

        Raises:
            EeroAuthenticationException: If verification fails
            EeroNetworkException: If there's a network error
        """
        if not self._user_token:
            raise EeroAuthenticationException("No user token available. Login first.")

        try:
            # Create a new session with the proper cookie
            cookies = {"s": self._user_token}

            # Log the verification attempt
            _LOGGER.debug(f"Verifying with token: {self._user_token}")
            _LOGGER.debug(f"Verification code: {verification_code}")
            _LOGGER.debug(f"Cookies: {cookies}")

            # Make the verification request
            async with self.session.post(
                LOGIN_VERIFY_ENDPOINT,
                cookies=cookies,
                json={"code": verification_code},
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(
                    f"Verification response status: {response.status}, body: {response_text}"
                )

                if response.status == 200:
                    # Per the workflow, the user_token becomes the session token
                    self._session_id = self._user_token

                    # Extract user and network data if available
                    try:
                        data = await response.json()
                        response_data = data.get("data", {})

                        # Extract network ID if available
                        networks = response_data.get("networks", {}).get("data", [])
                        if networks and len(networks) > 0:
                            network_url = networks[0].get("url", "")
                            if network_url:
                                network_id = network_url.split("/")[-1]
                                self._preferred_network_id = network_id
                                _LOGGER.debug(f"Set preferred network ID: {network_id}")
                    except Exception as e:
                        _LOGGER.warning(f"Error parsing verification response: {e}")

                    # Set expiry to 30 days from now (typical session length)
                    self._session_expiry = datetime.now().replace(
                        microsecond=0
                    ) + timedelta(days=30)

                    # Update session cookie for future requests
                    if self._session_id:
                        self.session.cookie_jar.update_cookies({"s": self._session_id})
                        _LOGGER.debug(f"Updated session cookie: s={self._session_id}")
                        await self._save_cookies()
                        return True

                    _LOGGER.error("Verification succeeded but no session ID was set")
                    return False
                else:
                    # Check for specific error codes
                    try:
                        error_data = await response.json()
                        meta = error_data.get("meta", {})
                        error_code = meta.get("code")
                        error_msg = meta.get("error")

                        if (
                            error_code == 401
                            and "verification code is incorrect"
                            in str(error_msg).lower()
                        ):
                            # Code was incorrect - may need to resend
                            _LOGGER.error(f"Verification code incorrect: {error_msg}")
                            raise EeroAuthenticationException(
                                f"Verification code incorrect: {error_msg}"
                            )
                        else:
                            _LOGGER.error(f"Verification failed: {meta}")
                            raise EeroAuthenticationException(
                                f"Verification failed: {meta}"
                            )
                    except json.JSONDecodeError:
                        _LOGGER.error(
                            f"Verification failed with non-JSON response: {response_text}"
                        )
                        raise EeroAuthenticationException(
                            f"Verification failed: {response.status} - {response_text}"
                        )
        except aiohttp.ClientError as err:
            error_msg = f"Network error during verification: {err}"
            _LOGGER.error(error_msg)
            raise EeroNetworkException(error_msg) from err

    async def resend_verification_code(self) -> bool:
        """Resend the verification code.

        Returns:
            True if resend was successful

        Raises:
            EeroAuthenticationException: If resend fails
            EeroNetworkException: If there's a network error
        """
        if not self._user_token:
            raise EeroAuthenticationException("No user token available. Login first.")

        try:
            # Create a new session with the proper cookie
            cookies = {"s": self._user_token}

            _LOGGER.debug(f"Resending verification code with token: {self._user_token}")

            # Make the resend request
            async with self.session.post(
                f"{LOGIN_ENDPOINT}/resend",
                cookies=cookies,
                json={},
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(
                    f"Resend response status: {response.status}, body: {response_text}"
                )

                if response.status == 200:
                    _LOGGER.info("Verification code resent successfully")
                    return True
                else:
                    _LOGGER.error(
                        f"Failed to resend verification code: {response_text}"
                    )
                    return False
        except aiohttp.ClientError as err:
            error_msg = f"Network error during resend: {err}"
            _LOGGER.error(error_msg)
            raise EeroNetworkException(error_msg) from err

    async def logout(self) -> bool:
        """Log out from the Eero API.

        Returns:
            True if logout was successful

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroNetworkException: If there's a network error
        """
        if not self.is_authenticated:
            _LOGGER.warning("Attempted to logout when not authenticated")
            return False

        try:
            async with self.session.post(
                LOGOUT_ENDPOINT,
                json={},  # Empty payload for logout
            ) as response:
                if response.status == 200:
                    # Clear session data
                    self._user_token = None
                    self._session_id = None
                    self._refresh_token = None
                    self._session_expiry = None

                    # Clear cookies
                    self.session.cookie_jar.clear()

                    # Update cookie file
                    await self._save_cookies()
                    return True
                else:
                    response_text = await response.text()
                    _LOGGER.error(
                        "Logout failed with status %s: %s",
                        response.status,
                        response_text,
                    )
                    return False
        except aiohttp.ClientError as err:
            raise EeroNetworkException(f"Network error during logout: {err}") from err

    async def _refresh_session(self) -> bool:
        """Refresh the session using the refresh token.

        Returns:
            True if session refresh was successful

        Raises:
            EeroAuthenticationException: If refresh fails
            EeroNetworkException: If there's a network error
        """
        if not self._refresh_token:
            raise EeroAuthenticationException("No refresh token available")

        try:
            async with self.session.post(
                f"{ACCOUNT_ENDPOINT}/refresh",
                json={"refresh_token": self._refresh_token},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_data = data.get("data", {})
                    self._session_id = response_data.get(SESSION_TOKEN_KEY)
                    self._refresh_token = response_data.get("refresh_token")

                    # Set expiry to 30 days from now
                    self._session_expiry = datetime.now().replace(
                        microsecond=0
                    ) + timedelta(days=30)

                    # Update session cookie for future requests
                    if self._session_id:
                        self.session.cookie_jar.update_cookies({"s": self._session_id})
                        await self._save_cookies()
                        return True
                    return False
                else:
                    _LOGGER.error(
                        "Session refresh failed with status %s", response.status
                    )
                    # Clear all tokens on failure
                    self._user_token = None
                    self._session_id = None
                    self._refresh_token = None
                    self._session_expiry = None
                    await self._save_cookies()
                    return False
        except aiohttp.ClientError as err:
            raise EeroNetworkException(
                f"Network error during session refresh: {err}"
            ) from err

    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Eero API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: API endpoint URL
            **kwargs: Additional parameters to pass to the request

        Returns:
            JSON response data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
            EeroRateLimitException: If rate limited
            EeroNetworkException: If there's a network error
            EeroTimeoutException: If request times out
        """
        if not self.is_authenticated:
            raise EeroAuthenticationException("Not authenticated")

        # Check if session needs refresh
        if (
            self._session_expiry
            and datetime.now() > self._session_expiry
            and self._refresh_token
        ):
            _LOGGER.debug("Session expired, attempting to refresh")
            if not await self._refresh_session():
                raise EeroAuthenticationException("Session expired and refresh failed")

        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=30)

        # Ensure the session has the cookie
        if self._session_id:
            self.session.cookie_jar.update_cookies({"s": self._session_id})

        _LOGGER.debug(f"Request URL: {url}")
        _LOGGER.debug(f"Request method: {method}")
        _LOGGER.debug(f"Request cookies: {self.session.cookie_jar.filter_cookies(url)}")
        if "json" in kwargs:
            _LOGGER.debug(f"Request payload: {kwargs['json']}")

        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_text = await response.text()
                _LOGGER.debug(
                    f"Response status: {response.status}, body: {response_text}"
                )

                if response.status == 200:
                    try:
                        return await response.json()
                    except Exception as e:
                        _LOGGER.error(f"Error parsing JSON response: {e}")
                        raise EeroAPIException(
                            response.status, f"Invalid JSON response: {response_text}"
                        )
                elif response.status == 401:
                    raise EeroAuthenticationException(
                        f"Authentication failed: {response_text}"
                    )
                elif response.status == 429:
                    raise EeroRateLimitException("Rate limit exceeded")
                else:
                    raise EeroAPIException(response.status, response_text)
        except asyncio.TimeoutError as err:
            raise EeroTimeoutException("Request timed out") from err
        except aiohttp.ClientError as err:
            raise EeroNetworkException(f"Network error: {err}") from err

    async def get_account(self) -> Dict[str, Any]:
        """Get account information.

        Returns:
            Account information data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        response = await self._request("GET", ACCOUNT_ENDPOINT)
        return response.get("data", {})

    async def get_networks(self) -> List[Dict[str, Any]]:
        """Get list of networks.

        Returns:
            List of network data

        Raises:
            EeroAuthenticationException: If not authenticated
            EeroAPIException: If the API returns an error
        """
        response = await self._request("GET", f"{ACCOUNT_ENDPOINT}/networks")
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}"
        )
        return response.get("data", {})

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros"
        )
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros/{eero_id}"
        )
        return response.get("data", {})

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices"
        )
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}"
        )
        return response.get("data", {})

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles"
        )
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

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
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}"
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
        response = await self._request(
            "POST",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros/{eero_id}/reboot",
            json={},
        )
        return bool(response.get("meta", {}).get("code") == 200)

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
        payload: Dict[str, Any] = {"enabled": enabled}

        if name is not None:
            payload["name"] = name

        if password is not None:
            payload["password"] = password

        response = await self._request(
            "PUT",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/guest_network",
            json=payload,
        )
        return bool(response.get("meta", {}).get("code") == 200)

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
        response = await self._request(
            "PUT",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
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
        response = await self._request(
            "PUT",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
            json={"blocked": blocked},
        )
        return bool(response.get("meta", {}).get("code") == 200)

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
        response = await self._request(
            "PUT",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}",
            json={"paused": paused},
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
        response = await self._request(
            "POST",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/speedtest",
            json={},
        )
        return response.get("data", {})
