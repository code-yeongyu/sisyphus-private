"""InputBar component for TUI."""

from textual.events import Key
from textual.widgets import Input


class InputBar(Input):
    """메시지 입력창 위젯.

    Input 위젯을 상속하여 사용자 메시지 입력 및 전송 기능을 제공합니다.
    Enter 키로 메시지를 전송하고, UP 키로 미전송 메시지를 복원할 수 있습니다.
    """

    def __init__(self) -> None:
        """InputBar 위젯 초기화.

        플레이스홀더 텍스트와 미전송 메시지 저장소를 설정합니다.
        """
        super().__init__(
            id="input-bar",
            placeholder="Type a message... (Press Enter to send, UP to edit, Ctrl+C twice to quit)",
        )
        self._unsent_message: str = ""

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter 키 입력 시 메시지 큐에 추가.

        Args:
            event: Input.Submitted 이벤트 객체
        """
        message = event.value.strip()
        if message:
            # TODO: UserMessageEvent 정의 후 활성화
            # self.app.post_message(UserMessageEvent(message))

            # 임시 로그: 메시지가 큐에 추가되었음을 표시
            # Message queued: {message}

            self.value = ""
            self._unsent_message = ""

    def on_key(self, event: Key) -> None:
        """UP 화살표: 미전송 메시지 복원.

        Args:
            event: Key 이벤트 객체
        """
        if event.key == "up" and self._unsent_message:
            self.value = self._unsent_message
