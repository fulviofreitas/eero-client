"""Authentication API for Eero."""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import aiohttp
import keyring
from aiohttp import ClientSession

from ..const import (
    ACCOUNT_ENDPOINT,
    API_ENDPOINT,
    DEFAULT_HEADERS,
    LOGIN_ENDPOINT,
    LOGIN_VERIFY_ENDPOINT,
    LOGOUT_ENDPOINT,
    SESSION_TOKEN_KEY,
)
from ..exceptions import (
    EeroAPIException,
    EeroAuthenticationException,
    EeroNetworkException,
    EeroRateLimitException,
)
from .base import BaseAPI

_LOGGER = logging.getLogger(__name__)


class AuthAPI(BaseAPI):
    """Authentication API for Eero."""

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        cookie_file: Optional[str] = None,
        use_keyring: bool = True,
    ) -> None:
        """Initialize the AuthAPI.

        Args:
            session: Optional aiohttp ClientSession to use for requests
            cookie_file: Optional path to a file for storing authentication cookies
            use_keyring: Whether to use keyring for secure token storage
        """
        super().__init__(session, cookie_file, API_ENDPOINT)
        self._use_keyring = use_keyring
        self._user_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._session_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._preferred_network_id: Optional[str] = None
        self._session_expiry: Optional[datetime] = None
        self._login_in_progress = False

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        if self._session_id and self._session_expiry:
            # Check if session is expired
            if datetime.now() > self._session_expiry:
                _LOGGER.debug("Session expired")
                return False
            return True
        return False

    @property
    def preferred_network_id(self) -> Optional[str]:
        """Get the preferred network ID.

        Returns:
            Preferred network ID or None
        """
        return self._preferred_network_id

    @preferred_network_id.setter
    def preferred_network_id(self, value: str) -> None:
        """Set the preferred network ID.

        Args:
            value: Network ID to set as preferred
        """
        self._preferred_network_id = value
        # Save to storage when setting preferred network
        self._save_authentication_data()

    async def __aenter__(self) -> "AuthAPI":
        """Enter async context manager."""
        await super().__aenter__()
        await self._load_authentication_data()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def _load_authentication_data(self) -> None:
        """Load authentication data from storage."""
        if self._use_keyring:
            await self._load_from_keyring()
        elif self._cookie_file:
            await self._load_from_file()

    async def _save_authentication_data(self) -> None:
        """Save authentication data to storage."""
        if self._use_keyring:
            await self._save_to_keyring()
        elif self._cookie_file:
            await self._save_to_file()

    async def _load_from_keyring(self) -> None:
        """Load authentication data from keyring."""
        try:
            token_data = keyring.get_password("eero-client", "auth-tokens")
            if token_data:
                data = json.loads(token_data)
                self._user_token = data.get("user_token")
                self._refresh_token = data.get("refresh_token")
                self._session_id = data.get("session_id")
                self._user_id = data.get("user_id")
                self._preferred_network_id = data.get("preferred_network_id")

                expiry = data.get("session_expiry")
                if expiry:
                    self._session_expiry = datetime.fromisoformat(expiry)

                # Check for expiration
                if self._session_expiry and self._session_expiry < datetime.now():
                    _LOGGER.debug("Session expired, will need to refresh")
                    # Clear expired session
                    self._session_id = None
                    self._session_expiry = None
                    await self._save_to_keyring()
                elif self._session_id:
                    # Set the cookie in aiohttp format
                    self.session.cookie_jar.update_cookies({"s": self._session_id})
                    _LOGGER.debug(f"Loaded cookie from keyring: s={self._session_id}")
        except Exception as e:
            _LOGGER.debug(f"Error loading from keyring: {e}")

    async def _save_to_keyring(self) -> None:
        """Save authentication data to keyring."""
        try:
            data = {
                "user_token": self._user_token,
                "refresh_token": self._refresh_token,
                "session_id": self._session_id,
                "user_id": self._user_id,
                "preferred_network_id": self._preferred_network_id,
                "session_expiry": (
                    self._session_expiry.isoformat() if self._session_expiry else None
                ),
            }
            keyring.set_password("eero-client", "auth-tokens", json.dumps(data))
            _LOGGER.debug("Saved authentication data to keyring")
        except Exception as e:
            _LOGGER.error(f"Error saving to keyring: {e}")

    async def _load_from_file(self) -> None:
        """Load authentication data from file."""
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
                    _LOGGER.debug("Session expired, will need to refresh")
                    # Clear expired session
                    self._session_id = None
                    self._session_expiry = None
                    await self._save_to_file()
                elif self._session_id:
                    # Set the cookie in aiohttp format
                    self.session.cookie_jar.update_cookies({"s": self._session_id})
                    _LOGGER.debug(f"Loaded cookie from file: s={self._session_id}")
        except (FileNotFoundError, json.JSONDecodeError):
            _LOGGER.debug("No valid cookie file found at %s", self._cookie_file)

    async def _save_to_file(self) -> None:
        """Save authentication data to file."""
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

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self._cookie_file)), exist_ok=True)

        with open(self._cookie_file, "w") as f:
            json.dump(cookies, f)
            _LOGGER.debug(f"Saved authentication data to {self._cookie_file}")

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
        # Clear any previous authentication data
        self._user_token = None
        self._session_id = None
        self._refresh_token = None
        self._session_expiry = None
        self._login_in_progress = True

        # Save to ensure we don't have stale data
        await self._save_authentication_data()

        try:
            # Clear cookies to ensure fresh login
            self.session.cookie_jar.clear()

            _LOGGER.debug(f"Starting login with identifier: {user_identifier}")

            response = await self.post(
                LOGIN_ENDPOINT,
                json={"login": user_identifier},
            )

            # Extract user_token from the nested structure
            self._user_token = response.get("data", {}).get("user_token")
            _LOGGER.debug(f"Extracted user_token: {self._user_token}")

            if not self._user_token:
                _LOGGER.error("Login failed: No user token received")
                return False

            # Save the token
            await self._save_authentication_data()

            return bool(self._user_token)
        except EeroAPIException as err:
            _LOGGER.error(f"Login failed: {err}")
            raise EeroAuthenticationException(f"Login failed: {err}") from err
        except aiohttp.ClientError as err:
            error_msg = f"Network error during login: {err}"
            _LOGGER.error(error_msg)
            raise EeroNetworkException(error_msg) from err

    def _extract_network_id_from_response(self, response_data: Dict) -> Optional[str]:
        """Extract network ID from the response data.

        Args:
            response_data: Response data

        Returns:
            Network ID or None if not found
        """
        try:
            # Check for networks in the new format (networks list in data)
            networks = response_data.get("networks", {}).get("data", [])

            # If that's empty, try the old format (data.data array)
            if not networks:
                networks = response_data.get("data", [])

            # If still empty, bail out
            if not networks or not isinstance(networks, list) or len(networks) == 0:
                return None

            # Get the first network
            network = networks[0]

            # Try to get ID directly from the network
            network_id = network.get("id")
            if network_id:
                _LOGGER.debug(f"Found network ID directly: {network_id}")
                return network_id

            # Try to extract from URL
            network_url = network.get("url")
            if network_url:
                # URL format is usually "/2.2/networks/network_id"
                parts = network_url.split("/")
                if len(parts) > 0:
                    network_id = parts[-1]
                    _LOGGER.debug(f"Extracted network ID from URL: {network_id}")
                    return network_id
        except Exception as e:
            _LOGGER.warning(f"Error extracting network ID: {e}")

        # Couldn't find network ID
        return None

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
            # Log the verification attempt
            _LOGGER.debug(f"Verifying with token: {self._user_token}")
            _LOGGER.debug(f"Verification code: {verification_code}")

            # Make sure we have the user token set as a cookie
            cookies = {"s": self._user_token}
            self.session.cookie_jar.update_cookies(cookies)

            # Make the verification request
            response = await self.post(
                LOGIN_VERIFY_ENDPOINT,
                auth_token=self._user_token,
                json={"code": verification_code},
            )

            # Per the workflow, the user_token becomes the session token
            self._session_id = self._user_token

            # Set login not in progress
            self._login_in_progress = False

            # Extract user and network data if available
            try:
                response_data = response.get("data", {})
                _LOGGER.debug(f"Verification response data: {response_data}")

                # Extract network ID using helper method
                network_id = self._extract_network_id_from_response(response_data)
                if network_id:
                    self._preferred_network_id = network_id
                    _LOGGER.debug(f"Set preferred network ID: {network_id}")
            except Exception as e:
                _LOGGER.warning(f"Error parsing verification response: {e}")

            # Set expiry to 30 days from now (typical session length)
            self._session_expiry = datetime.now().replace(microsecond=0) + timedelta(
                days=30
            )

            # Update session cookie for future requests
            if self._session_id:
                self.session.cookie_jar.update_cookies({"s": self._session_id})
                _LOGGER.debug(f"Updated session cookie: s={self._session_id}")
                await self._save_authentication_data()
                return True

            _LOGGER.error("Verification succeeded but no session ID was set")
            return False

        except EeroAPIException as err:
            # Check for specific error codes
            if getattr(err, "status_code", 0) == 401:
                _LOGGER.error(f"Verification code incorrect")
                raise EeroAuthenticationException(
                    "Verification code incorrect"
                ) from err
            else:
                _LOGGER.error(f"Verification failed: {err}")
                raise EeroAuthenticationException(
                    f"Verification failed: {err}"
                ) from err
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
            _LOGGER.debug(f"Resending verification code with token: {self._user_token}")

            # Make sure we have the user token set as a cookie
            cookies = {"s": self._user_token}
            self.session.cookie_jar.update_cookies(cookies)

            # Make the resend request
            await self.post(
                f"{LOGIN_ENDPOINT}/resend",
                auth_token=self._user_token,
                json={},
            )

            _LOGGER.info("Verification code resent successfully")
            return True
        except EeroAPIException as err:
            _LOGGER.error(f"Failed to resend verification code: {err}")
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
            await self.post(
                LOGOUT_ENDPOINT,
                auth_token=self._session_id,
                json={},  # Empty payload for logout
            )

            # Clear session data
            self._user_token = None
            self._session_id = None
            self._refresh_token = None
            self._session_expiry = None

            # Clear cookies
            self.session.cookie_jar.clear()

            # Update storage
            await self._save_authentication_data()
            return True
        except EeroAPIException as err:
            _LOGGER.error(f"Logout failed: {err}")
            return False
        except aiohttp.ClientError as err:
            raise EeroNetworkException(f"Network error during logout: {err}") from err

    async def refresh_session(self) -> bool:
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
            response = await self.post(
                f"{ACCOUNT_ENDPOINT}/refresh",
                json={"refresh_token": self._refresh_token},
            )

            response_data = response.get("data", {})
            self._session_id = response_data.get(SESSION_TOKEN_KEY)
            self._refresh_token = response_data.get("refresh_token")

            # Set expiry to 30 days from now
            self._session_expiry = datetime.now().replace(microsecond=0) + timedelta(
                days=30
            )

            # Update session cookie for future requests
            if self._session_id:
                self.session.cookie_jar.update_cookies({"s": self._session_id})
                await self._save_authentication_data()
                return True
            return False
        except EeroAPIException as err:
            _LOGGER.error(f"Session refresh failed: {err}")
            # Clear all tokens on failure
            self._user_token = None
            self._session_id = None
            self._refresh_token = None
            self._session_expiry = None
            await self._save_authentication_data()
            return False
        except aiohttp.ClientError as err:
            raise EeroNetworkException(
                f"Network error during session refresh: {err}"
            ) from err

    async def ensure_authenticated(self) -> bool:
        """Ensure the client is authenticated, refreshing if necessary.

        Returns:
            True if authenticated, False otherwise
        """
        if not self.is_authenticated:
            return False

        # Check if session needs refresh
        if (
            self._session_expiry
            and datetime.now() > self._session_expiry
            and self._refresh_token
        ):
            _LOGGER.debug("Session expired, attempting to refresh")
            return await self.refresh_session()

        return True

    async def get_auth_token(self) -> Optional[str]:
        """Get the current authentication token.

        Returns:
            Current authentication token or None
        """
        if await self.ensure_authenticated():
            return self._session_id
        return None

    async def clear_auth_data(self) -> None:
        """Clear all authentication data."""
        self._user_token = None
        self._session_id = None
        self._refresh_token = None
        self._session_expiry = None
        self._login_in_progress = False

        # Clear cookies
        self.session.cookie_jar.clear()

        # Save cleared data
        await self._save_authentication_data()

        _LOGGER.debug("Cleared all authentication data")
