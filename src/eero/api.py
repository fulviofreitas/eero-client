"""API client for interacting with the Eero API with fixed authentication flow."""

import asyncio
import json
import logging
import re
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast
from pathlib import Path

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
            # Check if file exists
            cookie_path = Path(os.path.expanduser(self._cookie_file))
            if not cookie_path.exists():
                _LOGGER.debug(f"Cookie file not found: {self._cookie_file}")
                return

            # Check file permissions and size
            if not os.access(cookie_path, os.R_OK):
                _LOGGER.warning(f"Cannot read cookie file: {self._cookie_file}")
                return

            file_size = os.path.getsize(cookie_path)
            if file_size == 0:
                _LOGGER.debug(f"Cookie file is empty: {self._cookie_file}")
                return

            # Read and parse the file
            with open(cookie_path, "r") as f:
                content = f.read().strip()

                # Try to parse as JSON
                try:
                    cookies = json.loads(content)
                except json.JSONDecodeError as e:
                    _LOGGER.warning(f"Invalid JSON in cookie file: {e}")
                    return

                # Extract session data
                self._user_token = cookies.get("user_token")
                self._refresh_token = cookies.get("refresh_token")
                self._session_id = cookies.get("session_id")
                self._user_id = cookies.get("user_id")
                self._preferred_network_id = cookies.get("preferred_network_id")

                # Check if we have valid session data
                if not self._user_token and not self._session_id:
                    _LOGGER.debug("No valid authentication data found in cookie file")
                    return

                # Process expiry if present
                expiry = cookies.get("session_expiry")
                if expiry:
                    try:
                        self._session_expiry = datetime.fromisoformat(expiry)
                    except ValueError:
                        # Handle invalid date format
                        _LOGGER.warning(f"Invalid date format in cookie file: {expiry}")
                        self._session_expiry = None

                # If session is expired, clear tokens
                if self._session_expiry and self._session_expiry < datetime.now():
                    _LOGGER.debug("Session expired, clearing tokens")
                    self._user_token = None
                    self._session_id = None
                    return

                # Log the loaded cookie for debugging
                if self._session_id:
                    _LOGGER.debug(f"Loaded cookie: s={self._session_id}")

                # Note: We do NOT set cookies or headers here
                # Instead, we'll set them per-request as needed
        except Exception as e:
            _LOGGER.warning(f"Error loading cookies from {self._cookie_file}: {e}")

    async def _save_cookies(self) -> None:
        """Save authentication cookies to file."""
        if not self._cookie_file:
            return

        try:
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

            # Create directory if it doesn't exist
            cookie_path = Path(os.path.expanduser(self._cookie_file))
            cookie_path.parent.mkdir(parents=True, exist_ok=True)

            with open(cookie_path, "w") as f:
                json.dump(cookies, f)
                _LOGGER.debug(f"Saved cookies to {self._cookie_file}")
        except Exception as e:
            _LOGGER.warning(f"Error saving cookies to {self._cookie_file}: {e}")

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
        # Start fresh - clear any existing tokens
        self._user_token = None
        self._session_id = None
        self._refresh_token = None

        # Clean up phone number format if needed (remove spaces, dashes, etc.)
        if re.match(r"^\+?[0-9\s\-\(\)]+$", user_identifier):
            # This looks like a phone number, clean it up
            cleaned_number = re.sub(r"[^0-9]", "", user_identifier)
            # Add +1 country code if it's a 10-digit US number without country code
            if len(cleaned_number) == 10:
                user_identifier = f"+1{cleaned_number}"
            elif not user_identifier.startswith("+"):
                user_identifier = f"+{cleaned_number}"
            _LOGGER.debug(f"Cleaned phone number to: {user_identifier}")

        try:
            # Use a fresh set of headers for login
            login_headers = self._headers.copy()

            _LOGGER.debug(f"Login request: {LOGIN_ENDPOINT} with identifier: {user_identifier}")

            async with self.session.post(
                LOGIN_ENDPOINT,
                headers=login_headers,
                json={"login": user_identifier},
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    error_message = f"Login failed: {response.status}"
                    try:
                        error_data = await response.json()
                        if "meta" in error_data and "error" in error_data["meta"]:
                            error_message = f"Login failed: {error_data['meta']['error']}"
                    except:
                        error_message = f"Login failed: {response.status} - {response_text}"

                    _LOGGER.error(error_message)
                    raise EeroAuthenticationException(error_message)

                response_text = await response.text()
                _LOGGER.debug(f"Login response status: {response.status}, body: {response_text}")

                try:
                    data = await response.json()
                    # Extract user_token from the nested structure
                    self._user_token = data.get("data", {}).get("user_token")
                    _LOGGER.debug(f"Extracted user_token: {self._user_token}")

                    if self._user_token:
                        # Set session expiry to 5 minutes for verification window
                        self._session_expiry = datetime.now() + timedelta(minutes=5)
                        await self._save_cookies()
                        return True
                    else:
                        _LOGGER.error("No user token found in login response")
                        return False
                except json.JSONDecodeError:
                    _LOGGER.error(f"Invalid JSON in login response: {response_text}")
                    return False
        except aiohttp.ClientError as err:
            error_msg = f"Network error during login: {err}"
            _LOGGER.error(error_msg)
            raise EeroNetworkException(error_msg) from err

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
            # Create cookies for verification - this is the key part
            cookies = {"s": self._user_token}

            _LOGGER.debug(f"Verifying with token: {self._user_token}")
            _LOGGER.debug(f"Verification code: {verification_code}")
            _LOGGER.debug(f"Cookies: {cookies}")

            # Make the verification request with cookies (not headers)
            async with self.session.post(
                LOGIN_VERIFY_ENDPOINT,
                cookies=cookies,  # Use cookies parameter, not headers
                json={"code": verification_code},
                headers=self._headers,  # Still use default headers
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(
                    f"Verification response status: {response.status}, body: {response_text}"
                )

                if response.status == 200:
                    # On successful verification, the user_token becomes the session token
                    self._session_id = self._user_token

                    # Extract additional data if available
                    try:
                        data = await response.json()
                        response_data = data.get("data", {})

                        # Extract network ID if available
                        networks = response_data.get("networks", {}).get("data", [])
                        if networks and len(networks) > 0:
                            network_url = networks[0].get("url", "")
                            if network_url:
                                # Extract network ID from URL (format: /2.2/networks/NETWORK_ID)
                                parts = network_url.rstrip("/").split("/")
                                if len(parts) > 0:
                                    self._preferred_network_id = parts[-1]
                                    _LOGGER.debug(
                                        f"Set preferred network ID: {self._preferred_network_id}"
                                    )
                    except Exception as e:
                        _LOGGER.warning(f"Error parsing verification response: {e}")

                    # Set expiry to 30 days from now (typical session length)
                    self._session_expiry = datetime.now().replace(microsecond=0) + timedelta(
                        days=30
                    )

                    # Save the session
                    await self._save_cookies()
                    return True
                else:
                    # Check for specific error codes
                    try:
                        error_data = await response.json()
                        meta = error_data.get("meta", {})
                        error_code = meta.get("code")
                        error_msg = meta.get("error")

                        if error_code == 401 and "verification.invalid" in str(error_msg).lower():
                            # Code was incorrect
                            _LOGGER.error(f"Verification failed: {meta}")
                            raise EeroAuthenticationException(f"Verification failed: {meta}")
                        else:
                            _LOGGER.error(f"Verification failed: {meta}")
                            raise EeroAuthenticationException(f"Verification failed: {meta}")
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
            # Create cookies for resend request
            cookies = {"s": self._user_token}

            _LOGGER.debug(f"Resending verification code with token: {self._user_token}")

            # Make the resend request with cookies
            async with self.session.post(
                f"{LOGIN_ENDPOINT}/resend",
                cookies=cookies,  # Use cookies parameter, not headers
                json={},
                headers=self._headers,  # Still use default headers
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(f"Resend response status: {response.status}, body: {response_text}")

                if response.status == 200:
                    _LOGGER.info("Verification code resent successfully")
                    return True
                else:
                    _LOGGER.error(f"Failed to resend verification code: {response_text}")
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
            # Create cookies for logout request
            cookies = {"s": self._session_id}

            async with self.session.post(
                LOGOUT_ENDPOINT,
                cookies=cookies,  # Use cookies parameter, not headers
                json={},
                headers=self._headers,  # Still use default headers
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(f"Logout response status: {response.status}, body: {response_text}")

                if response.status == 200:
                    # Clear session data
                    self._user_token = None
                    self._session_id = None
                    self._refresh_token = None
                    self._session_expiry = None

                    # Update cookie file
                    await self._save_cookies()
                    return True
                else:
                    _LOGGER.error(
                        "Logout failed with status %s: %s", response.status, response_text
                    )
                    return False
        except aiohttp.ClientError as err:
            raise EeroNetworkException(f"Network error during logout: {err}") from err

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

        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=30)

        # Set cookies for this request
        cookies = kwargs.pop("cookies", {})
        if self._session_id and "s" not in cookies:
            cookies["s"] = self._session_id

        # Set headers from defaults
        headers = kwargs.pop("headers", {})
        merged_headers = self._headers.copy()
        merged_headers.update(headers)

        _LOGGER.debug(f"Request URL: {url}")
        _LOGGER.debug(f"Request method: {method}")
        _LOGGER.debug(f"Request cookies: {cookies}")
        if "json" in kwargs:
            _LOGGER.debug(f"Request payload: {kwargs['json']}")

        try:
            async with self.session.request(
                method, url, cookies=cookies, headers=merged_headers, **kwargs
            ) as response:
                response_text = await response.text()
                _LOGGER.debug(f"Response status: {response.status}, body: {response_text}")

                if response.status == 200:
                    try:
                        return await response.json()
                    except Exception as e:
                        _LOGGER.error(f"Error parsing JSON response: {e}")
                        raise EeroAPIException(
                            response.status, f"Invalid JSON response: {response_text}"
                        )
                elif response.status == 401:
                    # Authentication failed
                    error_message = "Authentication failed"
                    try:
                        error_data = await response.json()
                        if "meta" in error_data and "error" in error_data["meta"]:
                            error_message = f"Authentication failed: {error_data['meta']['error']}"
                    except:
                        error_message = (
                            f"Authentication failed: {response.status} - {response_text}"
                        )

                    raise EeroAuthenticationException(error_message)
                elif response.status == 429:
                    raise EeroRateLimitException("Rate limit exceeded")
                else:
                    error_message = f"API error: {response.status}"
                    try:
                        error_data = await response.json()
                        if "meta" in error_data and "error" in error_data["meta"]:
                            error_message = f"API error: {error_data['meta']['error']}"
                    except:
                        error_message = f"API error: {response.status} - {response_text}"

                    raise EeroAPIException(response.status, error_message)
        except asyncio.TimeoutError as err:
            raise EeroTimeoutException("Request timed out") from err
        except aiohttp.ClientError as err:
            raise EeroNetworkException(f"Network error: {err}") from err

    # The rest of the API methods remain the same but use the improved request method
    async def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        response = await self._request("GET", ACCOUNT_ENDPOINT)
        return response.get("data", {})

    async def get_networks(self) -> List[Dict[str, Any]]:
        """Get list of networks."""
        response = await self._request("GET", f"{ACCOUNT_ENDPOINT}/networks")
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

    async def get_network(self, network_id: str) -> Dict[str, Any]:
        """Get network information."""
        response = await self._request("GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}")
        return response.get("data", {})

    async def get_eeros(self, network_id: str) -> List[Dict[str, Any]]:
        """Get list of Eero devices."""
        response = await self._request("GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros")
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

    async def get_eero(self, network_id: str, eero_id: str) -> Dict[str, Any]:
        """Get information about a specific Eero device."""
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/eeros/{eero_id}"
        )
        return response.get("data", {})

    async def get_devices(self, network_id: str) -> List[Dict[str, Any]]:
        """Get list of connected devices."""
        response = await self._request("GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices")
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

    async def get_device(self, network_id: str, device_id: str) -> Dict[str, Any]:
        """Get information about a specific device."""
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}"
        )
        return response.get("data", {})

    async def get_profiles(self, network_id: str) -> List[Dict[str, Any]]:
        """Get list of profiles."""
        response = await self._request("GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles")
        return cast(List[Dict[str, Any]], response.get("data", {}).get("data", []))

    async def get_profile(self, network_id: str, profile_id: str) -> Dict[str, Any]:
        """Get information about a specific profile."""
        response = await self._request(
            "GET", f"{ACCOUNT_ENDPOINT}/networks/{network_id}/profiles/{profile_id}"
        )
        return response.get("data", {})

    async def reboot_eero(self, network_id: str, eero_id: str) -> bool:
        """Reboot an Eero device."""
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
        """Enable or disable the guest network."""
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

    async def set_device_nickname(self, network_id: str, device_id: str, nickname: str) -> bool:
        """Set a nickname for a device."""
        response = await self._request(
            "PUT",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
            json={"nickname": nickname},
        )
        return bool(response.get("meta", {}).get("code") == 200)

    async def block_device(self, network_id: str, device_id: str, blocked: bool) -> bool:
        """Block or unblock a device."""
        response = await self._request(
            "PUT",
            f"{ACCOUNT_ENDPOINT}/networks/{network_id}/devices/{device_id}",
            json={"blocked": blocked},
        )
        return bool(response.get("meta", {}).get("code") == 200)

    async def pause_profile(self, network_id: str, profile_id: str, paused: bool) -> bool:
        """Pause or unpause internet access for a profile."""
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
