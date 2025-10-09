"""Custom exceptions for Sisyphus."""

from __future__ import annotations


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
