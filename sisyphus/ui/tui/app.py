"""TUI application for Sisyphus."""

from datetime import datetime
from typing import TYPE_CHECKING

import anyio
from textual.app import App, ComposeResult
from textual.events import Key
from textual.message import Message

from sisyphus.core.tasks import TaskValidator
from sisyphus.ui.themes import THEMES
from sisyphus.ui.tui.components.chat_log import ChatLog
from sisyphus.ui.tui.components.input_bar import InputBar
from sisyphus.ui.tui.components.status_panel import StatusPanel
from sisyphus.ui.tui.events import AgentInterruptEvent, InputReadyEvent
from sisyphus.ui.tui.layouts.main import compose_main_layout
from sisyphus.utils.theme import ThemeName

if TYPE_CHECKING:
    from sisyphus.core.loop import ExecutionLoop
    from sisyphus.utils.types import AgentMessage


class UpdateStatusMessage(Message):
    """Status update message."""

    def __init__(self, status: str) -> None:
        """Initialize UpdateStatusMessage.

        Args:
            status: Status message
        """
        super().__init__()
        self.status = status


class ShowAgentMessage(Message):
    """Display agent message."""

    def __init__(self, message: "AgentMessage", source: str) -> None:
        """Initialize ShowAgentMessage.

        Args:
            message: Agent message
            source: Message source ('execute' or 'verify')
        """
        super().__init__()
        self.message = message
        self.source = source


class ShutdownRequestMessage(Message):
    """Shutdown request message (ExecutionLoop → TUI)."""

    pass


class CompletionMessage(Message):
    """Task completion message (ExecutionLoop → TUI).

    Displays completion message without closing the screen.
    """

    def __init__(self, message: str, elapsed_seconds: float | None = None) -> None:
        """Initialize CompletionMessage.

        Args:
            message: Completion message
            elapsed_seconds: Task elapsed time (seconds)
        """
        super().__init__()
        self.message = message
        self.elapsed_seconds = elapsed_seconds


class TUI(App[None]):
    """OpenCode-style TUI (UIProtocol implementation).

    Textual-based TUI that displays Execute/Verify progress in real-time
    and manages user input via message queue.
    """

    show_header = False
    show_footer = False
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Container {
        height: 90%;
    }

    #chat-scroll {
        height: 70%;
        border: solid $primary;
    }

    #status-container {
        height: 20%;
        border: solid $secondary;
    }

    #input-container {
        height: 10%;
        border: solid $accent;
    }

    #queue-display {
        height: auto;
        max-height: 5;
        color: $text-muted;
        background: $panel;
        padding: 0 1;
        text-style: italic;
    }

    #input-bar {
        min-height: 3;
        max-height: 10;
    }
    """

    BINDINGS = [
        ("ctrl+c", "interrupt", "Interrupt"),
        ("ctrl+d", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, theme: ThemeName = "mocha") -> None:
        """Initialize TUI app.

        Args:
            theme: Theme name ("mocha" | "latte")
        """
        super().__init__()
        self.theme_name = theme
        self.ctrl_c_count = 0
        self.last_ctrl_c_time: datetime | None = None
        self.shutdown_event = anyio.Event()
        self.ready_event = anyio.Event()
        self._input_ready_event = anyio.Event()
        self._initialized = False
        self.task_validator: TaskValidator | None = None
        self._last_total_checkboxes: int = 0
        self._last_completed_checkboxes: int = 0
        self.agent_interrupted = False
        self._execution_loop: ExecutionLoop | None = None

    def compose(self) -> ComposeResult:
        """Compose layout."""
        yield from compose_main_layout()

    def set_task_validator(self, task_validator: TaskValidator | None) -> None:
        """Set task validator for checkbox monitoring.

        Args:
            task_validator: TaskValidator instance to monitor ai-todolist.md
        """
        self.task_validator = task_validator

    def set_execution_loop(self, execution_loop: "ExecutionLoop") -> None:
        """Set execution loop for interrupt handling.

        Args:
            execution_loop: ExecutionLoop instance
        """
        self._execution_loop = execution_loop

    async def _monitor_todolist(self) -> None:
        """Background task to monitor ai-todolist.md changes.

        Polls the todolist file every 2 seconds and updates StatusPanel
        only when checkbox counts change.
        """
        if self.task_validator is None:
            return

        try:
            content = self.task_validator.read_content()
            if not content:
                return

            total = self.task_validator.count_total_checkboxes(content)
            completed = self.task_validator.count_completed_checkboxes(content)

            if total != self._last_total_checkboxes or completed != self._last_completed_checkboxes:
                self._last_total_checkboxes = total
                self._last_completed_checkboxes = completed

                status_panel = self.query_one(StatusPanel)
                status_panel.show_progress(completed, total)

        except FileNotFoundError:
            pass
        except Exception as e:
            self.log.error(f"Error monitoring todolist: {e}")

    async def on_mount(self) -> None:
        """Initialize."""

        mocha_theme = THEMES["mocha"]
        latte_theme = THEMES["latte"]

        self.register_theme(mocha_theme)
        self.register_theme(latte_theme)
        self.theme = self.theme_name

        if self.task_validator is not None:
            self.set_interval(2.0, self._monitor_todolist)

        self.ready_event.set()

    async def on_key(self, event: Key) -> None:
        """Handle Ctrl+C, Ctrl+D, Ctrl+Q.

        Args:
            event: Key event
        """
        if event.key == "ctrl+c":
            await self._handle_interrupt()
        elif event.key in ("ctrl+d", "ctrl+q"):
            await self._safe_shutdown()

    async def _handle_interrupt(self) -> None:
        """Handle Ctrl+C interrupt."""
        current_time = datetime.now()

        if self.last_ctrl_c_time and (current_time - self.last_ctrl_c_time).total_seconds() < 1.0:
            self.ctrl_c_count += 1

            if self.ctrl_c_count >= 2:
                await self._safe_shutdown()
        else:
            self.ctrl_c_count = 1
            self.last_ctrl_c_time = current_time
            status = self.query_one(StatusPanel)
            status.update_status("⚠️ Press Ctrl+C once more to exit")

    async def _safe_shutdown(self) -> None:
        """Safe shutdown procedure."""
        status = self.query_one(StatusPanel)
        status.update_status("🔄 Shutting down...")

        self.shutdown_event.set()
        self.exit()

    async def on_update_status_message(self, message: UpdateStatusMessage) -> None:
        """Status update handler."""
        try:
            status_panel = self.query_one(StatusPanel)
            status_panel.update_status(message.status)
        except Exception as e:
            self.log.error(f"Failed to update status: {e}")

    async def on_show_agent_message(self, message: ShowAgentMessage) -> None:
        """Agent message display handler."""
        try:
            chat_log = self.query_one(ChatLog)
            match message.source:
                case "execute":
                    chat_log.write_execute_message(message.message.content)
                case "verify":
                    chat_log.write_verify_message(message.message.content)
        except Exception as e:
            self.log.error(f"Failed to show message: {e}")

    async def on_shutdown_request_message(self, message: ShutdownRequestMessage) -> None:
        """Shutdown request handler."""
        await self._safe_shutdown()

    async def on_completion_message(self, message: CompletionMessage) -> None:
        """Task completion message handler."""
        try:
            chat_log = self.query_one(ChatLog)

            completion_text = message.message
            if message.elapsed_seconds is not None:
                elapsed_str = self._format_elapsed_time(message.elapsed_seconds)
                completion_text = f"{message.message} (Elapsed time: {elapsed_str})"

            chat_log.write_completion_message(completion_text)
            status_panel = self.query_one(StatusPanel)
            status_panel.update_status("✅ All tasks completed. Press Ctrl+C twice to exit.")
        except Exception as e:
            self.log.error(f"Failed to show completion message: {e}")

    def _format_elapsed_time(self, seconds: float) -> str:
        """Format elapsed time in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours} hour(s)")
        if minutes > 0:
            parts.append(f"{minutes} minute(s)")
        if secs > 0 or not parts:
            parts.append(f"{secs} second(s)")

        return " ".join(parts)

    async def on_agent_interrupt_event(self, message: AgentInterruptEvent) -> None:
        """Agent interrupt event handler."""
        self.agent_interrupted = True

        status_panel = self.query_one(StatusPanel)
        status_panel.update_status("⏸ Agent paused (resume by sending message)")

        if self._execution_loop is not None:
            self._execution_loop.request_interrupt()

        chat_log = self.query_one(ChatLog)
        chat_log.write("[yellow]⏸ Paused by ESC key. Send a message to resume.[/yellow]")

    async def on_input_ready_event(self, message: InputReadyEvent) -> None:
        """Wake up get_input() when Enter is pressed in InputBar."""
        if self.agent_interrupted:
            self.agent_interrupted = False
            status_panel = self.query_one(StatusPanel)
            status_panel.update_status("▶ Agent resumed")

            if self._execution_loop is not None:
                self._execution_loop.clear_interrupt()

        self._input_ready_event.set()

    # UIProtocol implementation
    async def initialize(self) -> None:
        """Initialize UI."""
        self._initialized = True

    async def show_message(self, message: "AgentMessage", source: str) -> None:
        """Display message (Thread-Safe).

        Args:
            message: Agent message to display
            source: Message source ('execute' or 'verify')
        """
        await self.ready_event.wait()
        self.post_message(ShowAgentMessage(message, source))

    async def show_status(self, status: str) -> None:
        """Display status (Thread-Safe).

        Args:
            status: Status message to display
        """
        await self.ready_event.wait()
        self.post_message(UpdateStatusMessage(status))

    async def get_input(self) -> str | None:
        """Get message from InputBar queue.

        Waits for next Enter if queue is empty.
        Automatically sends queued message when Agent calls this method.

        Returns:
            Queued message or None (on shutdown)
        """
        while True:
            try:
                input_bar = self.query_one(InputBar)
                queued = input_bar.get_and_clear_queue()
                if queued:
                    return queued

                await self._input_ready_event.wait()
                self._input_ready_event = anyio.Event()
            except Exception as e:
                self.log.error(f"Failed to get input: {e}")
                return None
