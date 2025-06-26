"""Base API client for Eero API interactions."""

import asyncio
import json
import logging
import os
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import aiohttp
from aiohttp import ClientSession

from ..const import DEFAULT_HEADERS, SESSION_TOKEN_KEY
from ..exceptions import (
    EeroAPIException,
    EeroAuthenticationException,
    EeroNetworkException,
    EeroRateLimitException,
    EeroTimeoutException,
)

_LOGGER = logging.getLogger(__name__)


class BaseAPI:
    """Base API client for interacting with RESTful APIs."""

    def __init__(
        self,
        session: Optional[ClientSession] = None,
        cookie_file: Optional[str] = None,
        base_url: str = "",
    ) -> None:
        """Initialize the BaseAPI.

        Args:
            session: Optional aiohttp ClientSession to use for requests
            cookie_file: Optional path to a file for storing authentication cookies
            base_url: Base URL for API endpoints
        """
        self._session = session
        self._cookie_file = cookie_file
        self._base_url = base_url
        self._headers = DEFAULT_HEADERS.copy()
        self._should_close_session = False

    async def __aenter__(self) -> "BaseAPI":
        """Enter async context manager."""
        if self._session is None:
            self._session = ClientSession()
            self._should_close_session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        if self._should_close_session and self._session:
            await self._session.close()

    @property
    def session(self) -> ClientSession:
        """Get the active aiohttp session or create a new one."""
        if self._session is None:
            self._session = ClientSession()
            self._should_close_session = True
        return self._session

    async def _request(
        self,
        method: str,
        url: str,
        auth_token: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: API endpoint URL
            auth_token: Optional authentication token
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
        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=30)

        # Add authentication token if provided
        if auth_token:
            cookies = {"s": auth_token}
            self.session.cookie_jar.update_cookies(cookies)
            _LOGGER.debug(f"Added auth cookie for request: {cookies}")

        # Make a full URL if a relative path was provided
        if not url.startswith(("http://", "https://")):
            url = f"{self._base_url.rstrip('/')}/{url.lstrip('/')}"

        # Enhanced request logging
        _LOGGER.debug(f"Request URL: {url}")
        _LOGGER.debug(f"Request method: {method}")
        _LOGGER.debug(f"Request cookies: {self.session.cookie_jar.filter_cookies(url)}")
        if "json" in kwargs:
            _LOGGER.debug(f"Request payload: {kwargs['json']}")

        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_text = await response.text()
                _LOGGER.debug(f"Response status: {response.status}")
                # _LOGGER.debug(
                #    f"Response body: {response_text[:500]}..."
                # )  # Log first 500 chars to avoid huge logs
                _LOGGER.debug(f"Response body: {response_text}")
                _LOGGER.debug(f"Response cookies: {response.cookies}")

                if response.status == 200:
                    try:
                        return await response.json()
                    except Exception as e:
                        _LOGGER.error(f"Error parsing JSON response: {e}")
                        raise EeroAPIException(
                            response.status, f"Invalid JSON response: {response_text}"
                        )
                elif response.status == 401:
                    _LOGGER.error(f"Authentication failed: {response_text}")
                    raise EeroAuthenticationException(f"Authentication failed: {response_text}")
                elif response.status == 404:
                    # Use debug level for 404s to reduce noise in CLI output
                    _LOGGER.debug(f"Resource not found at {url}: {response_text}")
                    raise EeroAPIException(
                        response.status,
                        f"Resource not found: {response_text}. URL: {url}",
                    )
                elif response.status == 429:
                    raise EeroRateLimitException("Rate limit exceeded")
                else:
                    _LOGGER.error(f"API error {response.status}: {response_text}")
                    raise EeroAPIException(response.status, response_text)
        except asyncio.TimeoutError as err:
            _LOGGER.error(f"Request to {url} timed out")
            raise EeroTimeoutException("Request timed out") from err
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error: {err} for URL: {url}")
            raise EeroNetworkException(f"Network error: {err}") from err

    async def get(self, url: str, auth_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Make a GET request to the API.

        Args:
            url: API endpoint URL
            auth_token: Optional authentication token
            **kwargs: Additional parameters to pass to the request

        Returns:
            JSON response data
        """
        return await self._request("GET", url, auth_token, **kwargs)

    async def post(self, url: str, auth_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Make a POST request to the API.

        Args:
            url: API endpoint URL
            auth_token: Optional authentication token
            **kwargs: Additional parameters to pass to the request

        Returns:
            JSON response data
        """
        return await self._request("POST", url, auth_token, **kwargs)

    async def put(self, url: str, auth_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Make a PUT request to the API.

        Args:
            url: API endpoint URL
            auth_token: Optional authentication token
            **kwargs: Additional parameters to pass to the request

        Returns:
            JSON response data
        """
        return await self._request("PUT", url, auth_token, **kwargs)

    async def delete(self, url: str, auth_token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request to the API.

        Args:
            url: API endpoint URL
            auth_token: Optional authentication token
            **kwargs: Additional parameters to pass to the request

        Returns:
            JSON response data
        """
        return await self._request("DELETE", url, auth_token, **kwargs)
