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
from sisyphus.ui.tui.events import InputReadyEvent
from sisyphus.ui.tui.layouts.main import compose_main_layout
from sisyphus.utils.theme import ThemeName

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


class UpdateStatusMessage(Message):
    """상태 업데이트 메시지."""

    def __init__(self, status: str) -> None:
        """Initialize UpdateStatusMessage.

        Args:
            status: 상태 메시지
        """
        super().__init__()
        self.status = status


class ShowAgentMessage(Message):
    """에이전트 메시지 표시."""

    def __init__(self, message: "AgentMessage", source: str) -> None:
        """Initialize ShowAgentMessage.

        Args:
            message: 에이전트 메시지
            source: 메시지 소스 ('execute' or 'verify')
        """
        super().__init__()
        self.message = message
        self.source = source


class ShutdownRequestMessage(Message):
    """종료 요청 메시지 (ExecutionLoop → TUI)."""

    pass


class CompletionMessage(Message):
    """작업 완료 메시지 (ExecutionLoop → TUI).

    화면을 닫지 않고 완료 메시지만 표시합니다.
    """

    def __init__(self, message: str, elapsed_seconds: float | None = None) -> None:
        """Initialize CompletionMessage.

        Args:
            message: 완료 메시지
            elapsed_seconds: 작업 소요 시간 (초)
        """
        super().__init__()
        self.message = message
        self.elapsed_seconds = elapsed_seconds


class TUI(App[None]):
    """OpenCode 스타일 TUI (UIProtocol 구현).

    Textual 기반 TUI로 Execute/Verify 진행상황을 실시간 표시하고
    사용자 입력을 메시지 큐로 관리합니다.
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
        height: auto;
        min-height: 1;
    }
    """

    BINDINGS = [
        ("ctrl+c", "interrupt", "Interrupt"),
        ("ctrl+d", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, theme: ThemeName = "mocha") -> None:
        """TUI 앱 초기화.

        Args:
            theme: 테마 이름 ("mocha" | "latte")
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

    def compose(self) -> ComposeResult:
        """레이아웃 구성."""
        yield from compose_main_layout()

    def set_task_validator(self, task_validator: TaskValidator | None) -> None:
        """Set task validator for checkbox monitoring.

        Args:
            task_validator: TaskValidator instance to monitor ai-todolist.md
        """
        self.task_validator = task_validator

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
        """초기화."""

        mocha_theme = THEMES["mocha"]
        latte_theme = THEMES["latte"]

        self.register_theme(mocha_theme)
        self.register_theme(latte_theme)
        self.theme = self.theme_name

        if self.task_validator is not None:
            self.set_interval(2.0, self._monitor_todolist)

        self.ready_event.set()

    async def on_key(self, event: Key) -> None:
        """Ctrl+C, Ctrl+D, Ctrl+Q 처리.

        Args:
            event: 키 이벤트
        """
        if event.key == "ctrl+c":
            await self._handle_interrupt()
        elif event.key in ("ctrl+d", "ctrl+q"):
            await self._safe_shutdown()

    async def _handle_interrupt(self) -> None:
        """Ctrl+C 인터럽트 처리."""
        current_time = datetime.now()

        if self.last_ctrl_c_time and (current_time - self.last_ctrl_c_time).total_seconds() < 1.0:
            self.ctrl_c_count += 1

            if self.ctrl_c_count >= 2:
                await self._safe_shutdown()
        else:
            self.ctrl_c_count = 1
            self.last_ctrl_c_time = current_time
            status = self.query_one(StatusPanel)
            status.update_status("⚠️ Ctrl+C 한 번 더 누르면 종료됩니다")

    async def _safe_shutdown(self) -> None:
        """안전한 종료 절차."""
        status = self.query_one(StatusPanel)
        status.update_status("🔄 종료 중...")

        self.shutdown_event.set()
        self.exit()

    async def on_update_status_message(self, message: UpdateStatusMessage) -> None:
        """상태 업데이트 핸들러."""
        try:
            status_panel = self.query_one(StatusPanel)
            status_panel.update_status(message.status)
        except Exception as e:
            self.log.error(f"Failed to update status: {e}")

    async def on_show_agent_message(self, message: ShowAgentMessage) -> None:
        """에이전트 메시지 표시 핸들러."""
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
        """종료 요청 핸들러."""
        await self._safe_shutdown()

    async def on_completion_message(self, message: CompletionMessage) -> None:
        """작업 완료 메시지 핸들러."""
        try:
            chat_log = self.query_one(ChatLog)

            completion_text = message.message
            if message.elapsed_seconds is not None:
                elapsed_str = self._format_elapsed_time(message.elapsed_seconds)
                completion_text = f"{message.message} (소요 시간: {elapsed_str})"

            chat_log.write_completion_message(completion_text)
            status_panel = self.query_one(StatusPanel)
            status_panel.update_status("✅ 모든 작업이 완료되었습니다. Ctrl+C 두 번으로 종료할 수 있습니다.")
        except Exception as e:
            self.log.error(f"Failed to show completion message: {e}")

    def _format_elapsed_time(self, seconds: float) -> str:
        """Format elapsed time in human-readable Korean format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}시간")
        if minutes > 0:
            parts.append(f"{minutes}분")
        if secs > 0 or not parts:
            parts.append(f"{secs}초")

        return " ".join(parts)

    async def on_input_ready_event(self, message: InputReadyEvent) -> None:
        """InputBar에서 Enter 눌렀을 때 get_input() 깨우기."""
        self._input_ready_event.set()

    # UIProtocol 구현
    async def initialize(self) -> None:
        """UI 초기화."""
        self._initialized = True

    async def show_message(self, message: "AgentMessage", source: str) -> None:
        """메시지 표시 (Thread-Safe).

        Args:
            message: 표시할 에이전트 메시지
            source: 메시지 소스 ('execute' or 'verify')
        """
        await self.ready_event.wait()
        self.post_message(ShowAgentMessage(message, source))

    async def show_status(self, status: str) -> None:
        """상태 표시 (Thread-Safe).

        Args:
            status: 표시할 상태 메시지
        """
        await self.ready_event.wait()
        self.post_message(UpdateStatusMessage(status))

    async def get_input(self) -> str | None:
        """InputBar 큐에서 메시지를 가져옴.

        큐가 비어있으면 다음 Enter를 대기합니다.
        Agent가 이 메서드를 호출하면 자동으로 큐잉된 메시지를 전송합니다.

        Returns:
            큐잉된 메시지 또는 None (종료 시)
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
