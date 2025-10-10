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

    def compose(self) -> ComposeResult:
        """위젯 구성.

        Returns:
            큐 표시 위젯과 입력 위젯
        """
        yield Static("", id="queue-display", classes="queue-hint")
        yield Input(
            placeholder="Type and press Enter to queue (UP to edit)",
            id="input-bar",
        )

    def on_mount(self) -> None:
        """위젯이 마운트될 때 큐 표시 초기화 및 Input에 focus 설정."""
        self._update_queue_display()
        input_widget = self.query_one("#input-bar", Input)
        self.call_after_refresh(input_widget.focus)
        self.log.info("InputBar mounted, setting focus on input widget")

    @on(Input.Submitted, "#input-bar")
    def handle_input_submitted(self, event: Input.Submitted) -> None:
        """Enter 키 입력 시 메시지를 큐에 추가.

        Args:
            event: Input.Submitted 이벤트 객체
        """
        message = event.value.strip()
        if message:
            if self._queued_message:
                self._queued_message += "\n" + message
            else:
                self._queued_message = message

            event.input.value = ""

            self._update_queue_display()
            self.app.post_message(InputReadyEvent())

        event.stop()

    def _update_queue_display(self) -> None:
        """큐잉된 메시지 표시를 업데이트."""
        try:
            queue_display = self.query_one("#queue-display", Static)
        except Exception:
            return

        if self._queued_message:
            lines = self._queued_message.split("\n")
            preview = "\n".join(lines[:3])
            if len(lines) > 3:
                preview += f"\n... ({len(lines) - 3} more lines)"
            queue_display.update(f"[Queue] {preview}\n[Press UP to edit]")
            queue_display.display = True
        else:
            queue_display.update("")
            queue_display.display = False

    async def on_key(self, event: Key) -> None:
        """키 이벤트 처리 (UP 키).

        Args:
            event: Key 이벤트 객체
        """
        try:
            input_widget = self.query_one("#input-bar", Input)
        except Exception:
            return

        self.log.info(f"on_key called: key={event.key}")

        if event.key == "up":
            if self._queued_message:
                input_widget.value = self._queued_message
                self._queued_message = ""
                self._update_queue_display()
            elif self._last_sent:
                input_widget.value = self._last_sent
            event.prevent_default()
            event.stop()

    def get_and_clear_queue(self) -> str | None:
        """큐잉된 메시지를 반환하고 큐를 비움.

        Returns:
            큐잉된 메시지 또는 None (큐 비어있을 때)
        """
        if self._queued_message:
            msg = self._queued_message
            self._queued_message = ""
            self._last_sent = msg
            self._update_queue_display()
            return msg
        return None
