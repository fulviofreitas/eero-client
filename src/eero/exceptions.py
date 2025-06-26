"""Exceptions for the Eero client package."""


class EeroException(Exception):
    """Base exception for all Eero client errors."""

    pass


class EeroAuthenticationException(EeroException):
    """Exception raised for authentication errors."""

    pass


class EeroRateLimitException(EeroException):
    """Exception raised when rate limited by the API."""

    pass


class EeroNetworkException(EeroException):
    """Exception raised for network-related errors."""

    pass


class EeroAPIException(EeroException):
    """Exception raised for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class EeroTimeoutException(EeroException):
    """Exception raised when a request times out."""

    pass
