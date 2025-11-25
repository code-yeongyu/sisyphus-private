"""CLI UI implementation using Rich Console."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from sisyphus_core.utils.types import AgentMessage

TOOL_ICONS: dict[str, str] = {
    "read": "📖",
    "write": "✏️",
    "edit": "📝",
    "bash": "💻",
    "bashoutput": "📤",
    "killshell": "🛑",
    "glob": "🔍",
    "grep": "🔎",
    "webfetch": "🌐",
    "websearch": "🌍",
    "task": "🤖",
    "todowrite": "📋",
    "notebookedit": "📓",
    "askuserquestion": "❓",
    "enterplanmode": "📐",
    "exitplanmode": "✅",
    "skill": "⚡",
    "slashcommand": "⌨️",
    "mcp__context7__resolve-library-id": "📚",
    "mcp__context7__get-library-docs": "📚",
}
DEFAULT_TOOL_ICON = "🔧"
TOOL_USE_PATTERN = re.compile(
    r"\[TOOL_USE:\s*(\w+)\].*?```json\s*\n(.*?)\n\s*```",
    re.DOTALL,
)


class CLI:
    """CLI UI implementation using Rich Console.

    Implements UIProtocol for command-line interface mode.
    Uses Rich for colored output and markdown rendering.
    """

    def __init__(self) -> None:
        """Initialize CLI with Rich Console."""
        # Use very large width for non-TTY environments (CI/CD) to prevent unwanted line breaks
        # For TTY environments, use default terminal width
        width = None if sys.stdout.isatty() else 1000
        self.console = Console(width=width, soft_wrap=True)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize CLI (no-op for console)."""
        self._initialized = True

    def _build_tool_table(self, tool_name: str, data: dict[str, object]) -> Table:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("key", style="dim")
        table.add_column("value")

        no_truncate_tools = {"bash"}
        for key, value in data.items():
            if tool_name in no_truncate_tools:
                display_value = value
            else:
                display_value = value[:77] + "..." if isinstance(value, str) and len(value) > 80 else value
            table.add_row(key, str(display_value))

        return table

    def _try_format_tool_message(self, content: str) -> tuple[str, Table | None] | None:
        match = TOOL_USE_PATTERN.search(content)
        if not match:
            return None

        tool_name = match.group(1).lower()
        json_content = match.group(2)
        json_content = "\n".join(line.strip() for line in json_content.split("\n"))

        try:
            data = json.loads(json_content)
        except json.JSONDecodeError:
            return None

        icon = TOOL_ICONS.get(tool_name, DEFAULT_TOOL_ICON)
        display_name = tool_name.capitalize()
        header = f"{icon} {display_name}"

        if not data:
            return (header, None)

        table = self._build_tool_table(tool_name, data)
        return (header, table)

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

        if not message.content:
            self.console.print(f"[dim]{timestamp}[/dim] [{color}]{source.upper()}:[/{color}]")
            return

        result = self._try_format_tool_message(message.content)
        if result:
            header, table = result
            self.console.print(f"[dim]{timestamp}[/dim] [{color}]{source.upper()}:[/{color}] {header}")
            if table:
                self.console.print(table)
        else:
            self.console.print(f"[dim]{timestamp}[/dim] [{color}]{source.upper()}:[/{color}]", end=" ")
            md = Markdown(message.content)
            self.console.print(md)

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

    async def show_phase_header(self, phase: str) -> None:
        match phase:
            case "execute":
                title = "▶ EXECUTE PHASE"
                style = "yellow"
            case "verify":
                title = "✓ VERIFY PHASE"
                style = "cyan"
            case _:
                title = f"▶ {phase.upper()} PHASE"
                style = "white"

        self.console.print()
        self.console.print(Panel(title, style=style, padding=(0, 2)))
