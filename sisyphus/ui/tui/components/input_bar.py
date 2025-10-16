"""InputBar component for TUI."""

from textual.events import Key
from textual.widgets import Input

from sisyphus.ui.tui.events import AgentInterruptEvent, InputReadyEvent


class InputBar(Input):
    """메시지 입력창 위젯.

    Enter 키로 메시지를 큐에 추가하고, Agent가 get_input() 호출하면 전달됩니다.
    UP 키로 큐잉된 메시지 또는 마지막 전송 메시지를 편집할 수 있습니다.
    ESC 키로 에이전트를 일시 중단할 수 있습니다.
    큐 상태는 placeholder에 표시됩니다.
    """

    def __init__(self) -> None:
        """InputBar 위젯 초기화."""
        super().__init__(
            placeholder="메시지를 입력하세요... (ESC: 중단)",
            id="input-bar",
        )
        self._queued_message: str = ""
        self._last_sent: str = ""
        self._original_placeholder = "메시지를 입력하세요... (ESC: 중단)"
        self._agent_paused = False

    def on_mount(self) -> None:
        """위젯이 마운트될 때 focus 설정."""
        self.call_after_refresh(self.focus)

    def on_input_submitted(self, event: Input.Submitted) -> None:
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
        """큐 상태를 placeholder에 표시."""
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
        """키 이벤트 처리 (UP 키, ESC 키).

        Args:
            event: Key 이벤트 객체
        """
        if event.key == "escape":
            event.stop()
            if not self._agent_paused:
                self._agent_paused = True
                self.placeholder = "⏸ 일시 중단됨 - 메시지 입력하면 재개"
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
        """큐잉된 메시지를 반환하고 큐를 비움.

        Returns:
            큐잉된 메시지 또는 None (큐 비어있을 때)
        """
        if self._queued_message:
            msg = self._queued_message
            self._queued_message = ""
            self._last_sent = msg
            self._update_placeholder()
            return msg
        return None
