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

    def _try_format_tool_message(self, content: str) -> str | None:
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

        if tool_name == "read":
            path = data.get("file_path", "")
            return f"{icon} Read → {path}"
        elif tool_name == "write":
            path = data.get("file_path", "")
            return f"{icon} Write → {path}"
        elif tool_name == "edit":
            path = data.get("file_path", "")
            return f"{icon} Edit → {path}"
        elif tool_name == "bash":
            cmd = data.get("command", "")
            cmd_preview = cmd[:60] + "..." if len(cmd) > 60 else cmd
            return f"{icon} Bash → {cmd_preview}"
        elif tool_name in ("glob", "grep"):
            pattern = data.get("pattern", "")
            return f"{icon} {tool_name.capitalize()} → {pattern}"
        elif tool_name == "webfetch":
            url = data.get("url", "")
            return f"{icon} WebFetch → {url}"
        elif tool_name == "websearch":
            query = data.get("query", "")
            return f"{icon} WebSearch → {query}"
        elif tool_name == "task":
            desc = data.get("description", "")
            return f"{icon} Task → {desc}"
        elif tool_name == "todowrite":
            return f"{icon} TodoWrite"
        else:
            return f"{icon} {tool_name}"

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

        compact = self._try_format_tool_message(message.content)
        if compact:
            self.console.print(f"[dim]{timestamp}[/dim] [{color}]{source.upper()}:[/{color}] {compact}")
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
