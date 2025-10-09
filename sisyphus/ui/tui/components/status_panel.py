"""StatusPanel component for TUI."""

from textual.widgets import RichLog


class StatusPanel(RichLog):
    """상태 패널 위젯.

    RichLog 위젯을 상속하여 작업 상태와 반복 진행률을 표시합니다.
    """

    def __init__(self) -> None:
        """StatusPanel 위젯 초기화.

        Rich 마크업, 구문 강조, 자동 스크롤 기능을 활성화합니다.
        """
        super().__init__(
            id="status-panel",
            highlight=True,
            markup=True,
            auto_scroll=True,
        )

    def update_status(self, status: str) -> None:
        """상태 업데이트.

        Args:
            status: 표시할 상태 메시지
        """
        self.write(f"[blue]{status}[/blue]")

    def show_iteration(self, current: int, total: int) -> None:
        """반복 진행률 표시.

        Args:
            current: 현재 반복 번호
            total: 전체 반복 횟수
        """
        self.write(f"[dim]Iteration {current}/{total}[/dim]")
