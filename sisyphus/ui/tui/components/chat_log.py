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

    def _should_auto_scroll(self) -> bool:
        """Check if auto-scroll should be active.

        Returns True if scroll position is near bottom (within 5-line buffer).
        This allows slight scroll-up without disabling auto-scroll.

        Returns:
            bool: True if should auto-scroll, False otherwise
        """
        return self.scroll_offset.y >= self.max_scroll_y - 5

    def write_user_message(self, content: str) -> None:
        """Display user message.

        Args:
            content: User message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}")
        if self._should_auto_scroll():
            self.call_after_refresh(self.scroll_end)

    def write_execute_message(self, content: str) -> None:
        """Write Execute message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [yellow]▶ EXECUTE:[/yellow] {content}")
        if self._should_auto_scroll():
            self.call_after_refresh(self.scroll_end)

    def write_verify_message(self, content: str) -> None:
        """Write Verify message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [cyan]✓ VERIFY:[/cyan] {content}")
        if self._should_auto_scroll():
            self.call_after_refresh(self.scroll_end)

    def write_completion_message(self, content: str) -> None:
        """Write task completion message.

        Args:
            content: Completion message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [bold green]✅ COMPLETED:[/bold green] {content}")
        if self._should_auto_scroll():
            self.call_after_refresh(self.scroll_end)
