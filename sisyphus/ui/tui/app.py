"""TUI application for Sisyphus."""

from datetime import datetime
from typing import TYPE_CHECKING

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from textual.app import App, ComposeResult
from textual.events import Key

from sisyphus.ui.tui.components.chat_log import ChatLog
from sisyphus.ui.tui.components.status_panel import StatusPanel
from sisyphus.ui.tui.layouts.main import compose_main_layout

if TYPE_CHECKING:
    from sisyphus.utils.types import AgentMessage


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

    #input-bar {
        height: 10%;
        border: solid $accent;
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
        self._send_stream: MemoryObjectSendStream[str] | None = None
        self._receive_stream: MemoryObjectReceiveStream[str] | None = None
        self._initialized = False

    def compose(self) -> ComposeResult:
        """레이아웃 구성."""
        yield from compose_main_layout()

    async def on_mount(self) -> None:
        """초기화."""
        self.title = "Sisyphus - Multi-Agent Execution System"
        self.sub_title = "Execute & Verify"

        # 메시지 큐 생성
        (
            self._send_stream,
            self._receive_stream,
        ) = anyio.create_memory_object_stream(max_buffer_size=100)

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

        # 메시지 큐 정리
        if self._send_stream:
            await self._send_stream.aclose()
        if self._receive_stream:
            await self._receive_stream.aclose()

        self.shutdown_event.set()
        self.exit()

    # UIProtocol 구현
    async def initialize(self) -> None:
        """UI 초기화."""
        self._initialized = True

    async def show_message(self, message: "AgentMessage", source: str) -> None:
        """메시지 표시.

        Args:
            message: 표시할 에이전트 메시지
            source: 메시지 소스 ('execute' or 'verify')
        """
        chat_log = self.query_one(ChatLog)
        match source:
            case "execute":
                chat_log.write_execute_message(message.content)
            case "verify":
                chat_log.write_verify_message(message.content)

    async def show_status(self, status: str) -> None:
        """상태 표시.

        Args:
            status: 표시할 상태 메시지
        """
        status_panel = self.query_one(StatusPanel)
        status_panel.update_status(status)

    async def get_input(self) -> str | None:
        """메시지 큐에서 입력 가져오기.

        Returns:
            사용자 입력 메시지 또는 None
        """
        if self._receive_stream:
            return await self._receive_stream.receive()
        return None

    async def close(self) -> None:
        """UI 종료."""
        await self._safe_shutdown()
