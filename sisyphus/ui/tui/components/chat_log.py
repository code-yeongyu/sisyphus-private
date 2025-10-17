"""ChatLog component for TUI."""

from datetime import datetime

from textual.widgets import RichLog


class ChatLog(RichLog):
    """채팅/진행상황 로그 위젯.

    RichLog 위젯을 상속하여 Execute/Verify 메시지를 색상으로 구분하여 표시합니다.
    사용자가 스크롤을 올리면 자동 스크롤을 중지하고, 맨 아래로 내리면 다시 자동 스크롤을 활성화합니다.
    """

    def __init__(self) -> None:
        """ChatLog 위젯 초기화.

        Rich 마크업, 구문 강조 기능을 활성화하고, 자동 스크롤은 조건부로 동작합니다.
        """
        super().__init__(
            id="chat-log",
            highlight=True,
            markup=True,
            auto_scroll=False,  # 자동 스크롤 비활성화
            wrap=True,
        )
        self._user_scrolling = False

    def watch_scroll_y(self, old_value: float, new_value: float) -> None:
        """스크롤 Y 위치 변경 감지.

        Args:
            old_value: 이전 스크롤 Y 위치
            new_value: 새로운 스크롤 Y 위치
        """
        # 맨 아래 근처인지 확인 (1픽셀 여유)
        if new_value >= self.max_scroll_y - 1:
            self._user_scrolling = False
        else:
            self._user_scrolling = True

    def _auto_scroll_if_needed(self) -> None:
        """필요시 자동 스크롤.

        사용자가 스크롤을 올리지 않은 상태(맨 아래)에서만 자동으로 스크롤합니다.
        """
        if not self._user_scrolling:
            self.scroll_end()

    def write_user_message(self, content: str) -> None:
        """사용자 메시지 표시.

        Args:
            content: 표시할 사용자 메시지 내용
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [green]👤 USER:[/green] {content}")
        self.call_after_refresh(self._auto_scroll_if_needed)

    def write_execute_message(self, content: str) -> None:
        """Execute 메시지 작성.

        Args:
            content: 표시할 메시지 내용
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [yellow]▶ EXECUTE:[/yellow] {content}")
        self.call_after_refresh(self._auto_scroll_if_needed)

    def write_verify_message(self, content: str) -> None:
        """Verify 메시지 작성.

        Args:
            content: 표시할 메시지 내용
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [cyan]✓ VERIFY:[/cyan] {content}")
        self.call_after_refresh(self._auto_scroll_if_needed)

    def write_completion_message(self, content: str) -> None:
        """작업 완료 메시지 작성.

        Args:
            content: 표시할 완료 메시지 내용
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [bold green]✅ COMPLETED:[/bold green] {content}")
        self.call_after_refresh(self._auto_scroll_if_needed)
