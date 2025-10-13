"""CLI UI implementation using Rich Console."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


class CLI:
    """CLI UI implementation using Rich Console.

    Implements UIProtocol for command-line interface mode.
    Uses Rich for colored output and markdown rendering.
    """

    def __init__(self) -> None:
        """Initialize CLI with Rich Console."""
        self.console = Console()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize CLI (no-op for console)."""
        self._initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        """Display agent message with color coding by source.

        Args:
            message: Agent message to display
            source: Message source ('execute' or 'verify')
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        match source:
            case "execute":
                color = "yellow"
            case "verify":
                color = "cyan"
            case _:
                color = "white"

        self.console.print(f"[dim]{timestamp}[/dim] [{color}]{source.upper()}:[/{color}]", end=" ")

        if message.content:
            md = Markdown(message.content)
            self.console.print(md)
        else:
            self.console.print()

    async def show_status(self, status: str) -> None:
        """Display status message.

        Args:
            status: Status text to display
        """
        self.console.print(f"[blue]{status}[/blue]")

    async def get_input(self) -> str | None:
        """Get user input (not supported in CLI mode).

        Returns:
            None (CLI does not support interactive input)
        """
        return None
