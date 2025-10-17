"""Agent Protocol definition for Sisyphus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


@runtime_checkable
class Agent(Protocol):
    """Protocol that all agents must implement."""

    supports_interactive: bool

    @property
    def session_id(self) -> str | None:
        """Get current session ID (may be None before stream() receives it).

        Returns:
            Current session ID or None if not yet available
        """
        ...

    async def initialize(self) -> None:
        """Initialize the agent."""
        ...

    async def start_session(self, session_id: str | None = None) -> str:
        """Start or resume a session, returning the actual session ID."""
        ...

    async def send(self, message: str) -> None:
        """Send a message."""
        ...

    def stream(self) -> AsyncIterator[AgentMessage]:
        """Stream responses.

        Note: Implementations can use async generator functions (async def + yield).
        """
        ...

    async def close(self) -> None:
        """Cleanup resources."""
        ...
