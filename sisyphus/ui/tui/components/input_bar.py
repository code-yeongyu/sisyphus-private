"""InputBar component for TUI."""

from textual.events import Key
from textual.widgets import TextArea

from sisyphus.ui.tui.components.chat_log import ChatLog
from sisyphus.ui.tui.events import AgentInterruptEvent, InputReadyEvent


class InputBar(TextArea):
    """Message input widget.

    Adds messages to queue on Enter key, delivered when Agent calls get_input().
    UP key allows editing queued message or last sent message.
    ESC key pauses the agent.
    Shift+Enter inserts newline, Enter sends message.
    Queue status is displayed in suggestion.
    """

    def __init__(self) -> None:
        """Initialize InputBar widget."""
        super().__init__(
            id="input-bar",
        )
        self._queued_message: str = ""
        self._last_sent: str = ""
        self._original_suggestion = "Type a message... (ESC: pause)"
        self._agent_paused = False
        self.suggestion = self._original_suggestion

    def on_mount(self) -> None:
        """Set focus when widget is mounted."""
        self.call_after_refresh(self.focus)

    def _update_suggestion(self) -> None:
        """Display queue status in suggestion."""
        if self._queued_message:
            lines = self._queued_message.split("\n")
            preview = lines[0][:50]
            if len(lines[0]) > 50:
                preview += "..."
            if len(lines) > 1:
                preview += f" (+{len(lines) - 1} more)"
            self.suggestion = f"[Queued: {preview}] Press UP to edit"
        else:
            self.suggestion = self._original_suggestion

    async def on_key(self, event: Key) -> None:
        """Handle key events (Enter, Shift+Enter, UP, ESC).

        Args:
            event: Key event object with .key attribute
        """
        if event.character == "\n":
            self.insert("\n")
            event.prevent_default()
            event.stop()
            return

        if event.key == "enter":
            message = self.text.strip()
            if message:
                if self._queued_message:
                    self._queued_message += "\n" + message
                else:
                    self._queued_message = message

                try:
                    chat_log = self.app.query_one(ChatLog)
                    chat_log.write_user_message(message)
                except Exception as exception:
                    self.log.error(f"Failed to display user message: {exception}")

                self.text = ""
                self._update_suggestion()
                self.app.post_message(InputReadyEvent())

                if self._agent_paused:
                    self._agent_paused = False
                    self.suggestion = self._original_suggestion

                event.prevent_default()
                event.stop()
                return

        elif event.key == "escape":
            event.stop()
            if not self._agent_paused:
                self._agent_paused = True
                self.suggestion = "⏸ Paused - send message to resume"
                self.app.post_message(AgentInterruptEvent())
                self.log.info("Agent interrupted by ESC key")
            return

        elif event.key == "up":
            if self._queued_message:
                self.text = self._queued_message
                self._queued_message = ""
                self._update_suggestion()
            elif self._last_sent:
                self.text = self._last_sent
            event.prevent_default()
            event.stop()
            return

    def get_and_clear_queue(self) -> str | None:
        """Return queued message and clear queue.

        Returns:
            Queued message or None (when queue is empty)
        """
        if self._queued_message:
            msg = self._queued_message
            self._queued_message = ""
            self._last_sent = msg
            self._update_suggestion()
            return msg
        return None
