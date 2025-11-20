"""Custom exceptions for Sisyphus."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

# Regex patterns for session reset time parsing
_RESET_TIME_PATTERNS = [
    re.compile(r"resets?\s+(\d{1,2})pm", re.IGNORECASE),  # "resets 7pm"
    re.compile(r"resets?\s+(\d{1,2}):(\d{2})pm", re.IGNORECASE),  # "resets 7:30pm"
    re.compile(r"resets?\s+(\d{1,2})am", re.IGNORECASE),  # "resets 7am"
    re.compile(r"resets?\s+(\d{1,2}):(\d{2})am", re.IGNORECASE),  # "resets 7:30am"
    re.compile(r"resets?\s+(\d{1,2}):(\d{2})", re.IGNORECASE),  # "resets 19:00"
]


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


def parse_reset_time(message: str) -> datetime | None:
    """Parse reset time from session limit error message.

    Args:
        message: Error message (e.g., "Session limit reached ∙ resets 7pm")

    Returns:
        Reset time as datetime, or None if parsing failed

    Examples:
        >>> parse_reset_time("Session limit reached ∙ resets 7pm")
        datetime(2025, 10, 11, 19, 0, 0)
    """
    for pattern in _RESET_TIME_PATTERNS:
        match = pattern.search(message)
        if match:
            try:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0

                if "pm" in pattern.pattern:
                    if hour != 12:
                        hour += 12
                elif "am" in pattern.pattern and hour == 12:
                    hour = 0

                now = datetime.now().astimezone()
                reset_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if reset_time <= now:
                    reset_time += timedelta(days=1)

                return reset_time
            except (ValueError, IndexError):
                continue

    return None
