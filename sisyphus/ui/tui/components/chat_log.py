"""ChatLog component for TUI."""

from textual.widgets import RichLog


class ChatLog(RichLog):
    """채팅/진행상황 로그 위젯.

    RichLog 위젯을 상속하여 Execute/Verify 메시지를 색상으로 구분하여 표시합니다.
    """

    def __init__(self) -> None:
        """ChatLog 위젯 초기화.

        Rich 마크업, 구문 강조, 자동 스크롤 기능을 활성화합니다.
        """
        super().__init__(
            id="chat-log",
            highlight=True,
            markup=True,
            auto_scroll=True,
        )

    def write_execute_message(self, content: str) -> None:
        """Execute 메시지 작성.

        Args:
            content: 표시할 메시지 내용
        """
        self.write(f"[yellow]▶ EXECUTE:[/yellow] {content}")

    def write_verify_message(self, content: str) -> None:
        """Verify 메시지 작성.

        Args:
            content: 표시할 메시지 내용
        """
        self.write(f"[cyan]✓ VERIFY:[/cyan] {content}")
