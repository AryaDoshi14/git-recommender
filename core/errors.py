"""Custom exceptions for GitFlix core modules."""

from typing import Optional


class GitHubError(Exception):
    """Exception raised for GitHub API request failures or rate limits.

    Attributes:
        message: Human-readable error description.
        status: HTTP status code, if available.
        retry_after: Seconds to wait before retrying, if provided by API headers.
    """

    def __init__(
        self,
        message: str,
        status: Optional[int] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.retry_after = retry_after

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"GitHubError(message={self.message!r}, status={self.status}, retry_after={self.retry_after})"
