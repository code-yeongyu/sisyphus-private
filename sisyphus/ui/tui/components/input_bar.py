"""InputBar component for TUI."""

from textual.events import Key
from textual.widgets import Input

from sisyphus.ui.tui.events import AgentInterruptEvent, InputReadyEvent


class InputBar(Input):
    """Message input widget.

    Adds messages to queue on Enter key, delivered when Agent calls get_input().
    UP key allows editing queued message or last sent message.
    ESC key pauses the agent.
    Queue status is displayed in placeholder.
    """

    def __init__(self) -> None:
        """Initialize InputBar widget."""
        super().__init__(
            placeholder="Type a message... (ESC: pause)",
            id="input-bar",
        )
        self._queued_message: str = ""
        self._last_sent: str = ""
        self._original_placeholder = "Type a message... (ESC: pause)"
        self._agent_paused = False

    def on_mount(self) -> None:
        """Set focus when widget is mounted."""
        self.call_after_refresh(self.focus)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Add message to queue on Enter key press.

        Args:
            event: Input.Submitted event object
        """
        message = event.value.strip()
        if message:
            if self._queued_message:
                self._queued_message += "\n" + message
            else:
                self._queued_message = message

            try:
                from sisyphus.ui.tui.components.chat_log import ChatLog

                chat_log = self.app.query_one(ChatLog)
                chat_log.write_user_message(message)
            except Exception as exception:
                self.log.error(f"Failed to display user message: {exception}")

            self.value = ""
            self._update_placeholder()
            self.app.post_message(InputReadyEvent())

            if self._agent_paused:
                self._agent_paused = False
                self.placeholder = self._original_placeholder

    def _update_placeholder(self) -> None:
        """Display queue status in placeholder."""
        if self._queued_message:
            lines = self._queued_message.split("\n")
            preview = lines[0][:50]
            if len(lines[0]) > 50:
                preview += "..."
            if len(lines) > 1:
                preview += f" (+{len(lines) - 1} more)"
            self.placeholder = f"[Queued: {preview}] Press UP to edit"
        else:
            self.placeholder = self._original_placeholder

    async def on_key(self, event: Key) -> None:
        """Handle key events (UP key, ESC key).

        Args:
            event: Key event object
        """
        if event.key == "escape":
            event.stop()
            if not self._agent_paused:
                self._agent_paused = True
                self.placeholder = "⏸ Paused - send message to resume"
                self.app.post_message(AgentInterruptEvent())
                self.log.info("Agent interrupted by ESC key")
        elif event.key == "up":
            if self._queued_message:
                self.value = self._queued_message
                self._queued_message = ""
                self._update_placeholder()
            elif self._last_sent:
                self.value = self._last_sent
            event.prevent_default()
            event.stop()

    def get_and_clear_queue(self) -> str | None:
        """Return queued message and clear queue.

        Returns:
            Queued message or None (when queue is empty)
        """
        if self._queued_message:
            msg = self._queued_message
            self._queued_message = ""
            self._last_sent = msg
            self._update_placeholder()
            return msg
        return None
