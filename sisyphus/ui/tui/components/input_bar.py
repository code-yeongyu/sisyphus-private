"""InputBar component for TUI."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.widgets import Input, Static

from sisyphus.ui.tui.events import InputReadyEvent


class InputBar(Vertical):
    """메시지 입력창 위젯.

    Input 위젯과 큐잉 상태 표시를 포함하는 컨테이너입니다.
    Enter 키로 메시지를 큐에 추가하고, Agent가 get_input() 호출하면 전달됩니다.
    UP 키로 큐잉된 메시지 또는 마지막 전송 메시지를 편집할 수 있습니다.
    """

    def __init__(self) -> None:
        """InputBar 위젯 초기화."""
        super().__init__(id="input-container")
        self._queued_message: str = ""
        self._last_sent: str = ""
        self._input_widget: Input | None = None
        self._queue_display: Static | None = None

    def compose(self) -> ComposeResult:
        """위젯 구성.

        Returns:
            큐 표시 위젯과 입력 위젯
        """
        self._queue_display = Static("", id="queue-display", classes="queue-hint")
        self._input_widget = Input(
            placeholder="Type and press Enter to queue (UP to edit)",
            id="input-bar",
        )
        yield self._queue_display
        yield self._input_widget

    def on_mount(self) -> None:
        """위젯이 마운트될 때 Input에 focus 설정."""
        self._update_queue_display()
        self.query_one("#input-bar", Input).focus()

    @on(Input.Submitted, "#input-bar")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter 키 입력 시 메시지를 큐에 추가.

        Args:
            event: Input.Submitted 이벤트 객체
        """
        event.stop()
        message = event.value.strip()
        if message:
            # 큐에 메시지 누적 (개행으로 구분)
            if self._queued_message:
                self._queued_message += "\n" + message
            else:
                self._queued_message = message

            # 입력창 비우기
            if self._input_widget:
                self._input_widget.value = ""

            # 큐 표시 업데이트
            self._update_queue_display()

            # InputReadyEvent 발생 (get_input() 깨우기)
            self.app.post_message(InputReadyEvent())

    def _update_queue_display(self) -> None:
        """큐잉된 메시지 표시를 업데이트."""
        if self._queue_display:
            if self._queued_message:
                lines = self._queued_message.split("\n")
                preview = "\n".join(lines[:3])  # 최대 3줄만 표시
                if len(lines) > 3:
                    preview += f"\n... ({len(lines) - 3} more lines)"
                self._queue_display.update(f"[Queue] {preview}\n[Press UP to edit]")
                self._queue_display.display = True
            else:
                self._queue_display.update("")
                self._queue_display.display = False

    def on_key(self, event: Key) -> None:
        """키 이벤트 처리.

        Args:
            event: Key 이벤트 객체
        """
        if event.key == "up":
            # 큐 있으면 큐 로드, 없으면 _last_sent 로드
            if self._queued_message:
                # 큐를 입력창에 로드
                if self._input_widget:
                    self._input_widget.value = self._queued_message
                # 큐 비우기
                self._queued_message = ""
                self._update_queue_display()
            elif self._last_sent:
                # 마지막 전송 메시지 로드
                if self._input_widget:
                    self._input_widget.value = self._last_sent

    def get_and_clear_queue(self) -> str | None:
        """큐잉된 메시지를 반환하고 큐를 비움.

        Returns:
            큐잉된 메시지 또는 None (큐 비어있을 때)
        """
        if self._queued_message:
            msg = self._queued_message
            self._queued_message = ""
            self._last_sent = msg  # 마지막 전송 메시지 저장
            self._update_queue_display()
            return msg
        return None
