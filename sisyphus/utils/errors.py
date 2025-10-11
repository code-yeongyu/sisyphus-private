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


class SessionLimitError(SisyphusError):
    """Raised when API session limit is reached."""

    def __init__(self, message: str, reset_time: datetime | None = None) -> None:
        super().__init__(message)
        self.reset_time = reset_time
