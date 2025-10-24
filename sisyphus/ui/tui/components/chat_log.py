"""ChatLog component for TUI."""

from datetime import datetime

from textual.message import Message
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
            auto_scroll=False,
            wrap=True,
        )
        self._user_scrolled_up: bool = False
        self._programmatic_scrolling: bool = False

    def _should_auto_scroll(self) -> bool:
        """Check if auto-scroll should be active.

        Returns True only if user has not manually scrolled up AND scroll position
        is at the bottom (within 1px). This ensures auto-scroll is disabled when
        the user is reading previous messages and enabled when scrolled to bottom.

        Returns:
            bool: True if should auto-scroll, False otherwise
        """
        if self._user_scrolled_up:
            return False
        return self.scroll_offset.y >= self.max_scroll_y - 1

    def on_scroll(self, event: Message) -> None:
        """Handle scroll events to track user-initiated scrolling.

        When the user scrolls, this event handler is triggered. It updates the
        `_user_scrolled_up` flag to track whether the user has manually scrolled
        away from the bottom. This flag is used to disable auto-scrolling when
        the user is reading previous messages.

        The flag is set to False (enabling auto-scroll) when the scroll position
        reaches the bottom (within 1px), and set to True (disabling auto-scroll)
        when scrolled up from the bottom.

        Ignores scroll events caused by programmatic scrolling (e.g., scroll_end())
        to prevent interfering with user's scroll position preference.

        Args:
            event: The scroll event triggered by user input
        """
        # Ignore scroll events from programmatic scrolling
        if self._programmatic_scrolling:
            return

        # Check if scroll position is at the bottom (within 1px tolerance)
        if self.scroll_offset.y >= self.max_scroll_y - 1:
            # At bottom: enable auto-scroll
            self._user_scrolled_up = False
        else:
            # Scrolled up: disable auto-scroll
            self._user_scrolled_up = True

    def _safe_scroll_end(self) -> None:
        """Scroll to the end without triggering user scroll detection.

        This method sets the programmatic scrolling flag to prevent on_scroll
        from misinterpreting the programmatic scroll as a user action.
        """
        self._programmatic_scrolling = True
        self.scroll_end()
        self._programmatic_scrolling = False

    def write_user_message(self, content: str) -> None:
        """Display user message.

        Args:
            content: User message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}", scroll_end=False)
        if self._should_auto_scroll():
            self.call_after_refresh(self._safe_scroll_end)

    def write_execute_message(self, content: str) -> None:
        """Write Execute message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [yellow]▶ EXECUTE:[/yellow] {content}", scroll_end=False)
        if self._should_auto_scroll():
            self.call_after_refresh(self._safe_scroll_end)

    def write_verify_message(self, content: str) -> None:
        """Write Verify message.

        Args:
            content: Message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [cyan]✓ VERIFY:[/cyan] {content}", scroll_end=False)
        if self._should_auto_scroll():
            self.call_after_refresh(self._safe_scroll_end)

    def write_completion_message(self, content: str) -> None:
        """Write task completion message.

        Args:
            content: Completion message content to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [bold green]✅ COMPLETED:[/bold green] {content}", scroll_end=False)
        if self._should_auto_scroll():
            self.call_after_refresh(self._safe_scroll_end)
