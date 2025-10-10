"""TUI application for Sisyphus."""

from datetime import datetime
from typing import TYPE_CHECKING

import anyio
from textual.app import App, ComposeResult
from textual.events import Key
from textual.message import Message

from sisyphus.ui.tui.components.chat_log import ChatLog
from sisyphus.ui.tui.components.input_bar import InputBar
from sisyphus.ui.tui.components.status_panel import StatusPanel
from sisyphus.ui.tui.events import InputReadyEvent
from sisyphus.ui.tui.layouts.main import compose_main_layout

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


class TUI(App[None]):
    """OpenCode 스타일 TUI (UIProtocol 구현).

    Textual 기반 TUI로 Execute/Verify 진행상황을 실시간 표시하고
    사용자 입력을 메시지 큐로 관리합니다.
    """

    CSS = """
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
    ]

    def __init__(self) -> None:
        """TUI 앱 초기화."""
        super().__init__()
        self.ctrl_c_count = 0
        self.last_ctrl_c_time: datetime | None = None
        self.shutdown_event = anyio.Event()
        self.ready_event = anyio.Event()
        self._input_ready_event = anyio.Event()
        self._initialized = False

    def compose(self) -> ComposeResult:
        """레이아웃 구성."""
        yield from compose_main_layout()

    async def on_mount(self) -> None:
        """초기화."""
        self.title = "Sisyphus - Multi-Agent Execution System"
        self.sub_title = "Execute & Verify"

        self.ready_event.set()

    async def on_key(self, event: Key) -> None:
        """Ctrl+C 2회 처리.

        Args:
            event: 키 이벤트
        """
        if event.key == "ctrl+c":
            await self._handle_interrupt()

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

    async def close(self) -> None:
        """UI 종료."""
        await self._safe_shutdown()
