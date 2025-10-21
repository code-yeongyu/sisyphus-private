"""Custom exceptions for Sisyphus."""

from __future__ import annotations

from datetime import datetime


class SisyphusError(Exception):
    """Base exception for all Sisyphus errors."""


class AgentNotFoundError(SisyphusError):
    """Raised when agent binary is not found."""


class SessionResumeError(SisyphusError):
    """Raised when session resume operation fails."""


class ServerStartError(SisyphusError):
    """Raised when server fails to start."""


class ProcessTimeoutError(SisyphusError):
    """Raised when process operation times out."""


class HealthCheckError(SisyphusError):
    """Raised when health check fails."""


class RetryRequiredError(SisyphusError):
    """Base class for errors that require retry.

    This exception indicates that the operation failed in a transient way
    and should be retried. Subclasses include SessionLimitError and
    PromptTooLongError.
    """

    def __init__(self, message: str) -> None:
        """Initialize RetryRequiredError.

        Args:
            message: Human-readable error description
        """
        super().__init__(message)


class SessionLimitError(RetryRequiredError):
    """Raised when API session limit is reached."""

    def __init__(self, message: str, reset_time: datetime | None = None) -> None:
        super().__init__(message)
        self.reset_time = reset_time


class PromptTooLongError(RetryRequiredError):
    """Raised when prompt exceeds maximum length.

    This error occurs when the input prompt is too large for the model
    to process. The operation should be retried with a reduced prompt size.
    """

    def __init__(self, message: str) -> None:
        """Initialize PromptTooLongError.

        Args:
            message: Human-readable error description
        """
        super().__init__(message)
