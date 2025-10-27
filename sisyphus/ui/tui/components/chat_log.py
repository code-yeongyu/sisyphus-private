"""ChatLog component for TUI."""

from datetime import datetime

from textual.widgets import RichLog


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
        self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}")

    def write_execute_message(self, content: str) -> None:
        """Write Execute message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [yellow]▶ EXECUTE:[/yellow] {content}")

    def write_verify_message(self, content: str) -> None:
        """Write Verify message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [cyan]✓ VERIFY:[/cyan] {content}")

    def write_completion_message(self, content: str) -> None:
        """Write task completion message.

        Args:
            content: Completion message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [bold green]✅ COMPLETED:[/bold green] {content}")
