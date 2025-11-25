"""ChatLog component for TUI."""

import json
import re
from datetime import datetime

from rich.table import Table
from textual.widgets import RichLog

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


class ChatLog(RichLog):
    """Chat/progress log widget.

    Inherits from RichLog widget to display Execute/Verify messages with color distinction.
    Stops auto-scrolling when user scrolls up, resumes auto-scrolling when scrolled to bottom.
    """

    def __init__(self) -> None:
        """Initialize ChatLog widget.

        Enables Rich markup, syntax highlighting, and auto-scrolling.
        """
        super().__init__(
            id="chat-log",
            highlight=True,
            markup=True,
            auto_scroll=True,
            wrap=True,
        )

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

        return (header, table)

    def watch_scroll_y(self, old_value: float, new_value: float) -> None:
        """Monitor scroll position to control auto-scroll behavior.

        Disables auto-scroll when user scrolls up, re-enables when scrolled to bottom.

        Args:
            old_value: Previous scroll Y position
            new_value: Current scroll Y position
        """
        # Call parent implementation first
        super().watch_scroll_y(old_value, new_value)

        # No scrollable content - keep auto-scroll enabled
        if self.max_scroll_y == 0:
            if not self.auto_scroll:
                self.auto_scroll = True
            return

        # At bottom - enable auto-scroll
        if new_value >= self.max_scroll_y:
            if not self.auto_scroll:
                self.auto_scroll = True
        # Not at bottom - disable auto-scroll
        else:
            if self.auto_scroll:
                self.auto_scroll = False

    def write_user_message(self, content: str) -> None:
        """Display user message.

        Args:
            content: User message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        _ = self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}")

    def write_execute_message(self, content: str) -> None:
        """Write Execute message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        result = self._try_format_tool_message(content)
        if result:
            header, table = result
            _ = self.write(f"[dim]{timestamp}[/dim] [yellow]▶ EXECUTE:[/yellow] {header}")
            if table:
                _ = self.write(table)
        else:
            _ = self.write(f"[dim]{timestamp}[/dim] [yellow]▶ EXECUTE:[/yellow] {content}")

    def write_verify_message(self, content: str) -> None:
        """Write Verify message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        result = self._try_format_tool_message(content)
        if result:
            header, table = result
            _ = self.write(f"[dim]{timestamp}[/dim] [cyan]✓ VERIFY:[/cyan] {header}")
            if table:
                _ = self.write(table)
        else:
            _ = self.write(f"[dim]{timestamp}[/dim] [cyan]✓ VERIFY:[/cyan] {content}")

    def write_completion_message(self, content: str) -> None:
        """Write task completion message.

        Args:
            content: Completion message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        _ = self.write(f"[dim]{timestamp}[/dim] [bold green]✅ COMPLETED:[/bold green] {content}")
