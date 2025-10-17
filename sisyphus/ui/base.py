"""UI Protocol definition and factory function."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from sisyphus.utils.theme import ThemeName

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


@runtime_checkable
class UIProtocol(Protocol):
    """Protocol that UI implementations must follow.

    The UI manages its own lifecycle. ExecutionLoop does not
    interfere with the UI lifecycle, it only uses the interface to display messages and status.
    """

    async def initialize(self) -> None:
        """Initialize the UI."""
        ...

    async def show_message(self, message: AgentMessage, source: str) -> None:
        """Display a message (source: 'execute' or 'verify')."""
        ...

    async def show_status(self, status: str) -> None:
        """Display a status message."""
        ...

    async def get_input(self) -> str | None:
        """Get user input (TUI only, CLI returns None)."""
        ...


def create_ui(mode: str, theme: ThemeName | None = None) -> UIProtocol:
    """UI factory.

    Args:
        mode: UI mode ('tui' or 'cli')
        theme: TUI theme ("mocha" | "latte"), defaults if None

    Returns:
        UI instance implementing UIProtocol
    """
    if mode == "tui":
        from sisyphus.ui.tui import TUI

        return TUI(theme=theme or "mocha")
    else:
        from sisyphus.ui.cli import CLI

        return CLI()
