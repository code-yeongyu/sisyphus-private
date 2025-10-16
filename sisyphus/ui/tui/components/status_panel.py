"""StatusPanel component for TUI."""

from datetime import datetime

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
        """상태 업데이트 (타임스탬프 포함).

        Args:
            status: 표시할 상태 메시지
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [blue]{status}[/blue]")

    def show_iteration(self, current: int, total: int) -> None:
        """반복 진행률 표시 (타임스탬프 포함).

        Args:
            current: 현재 반복 번호
            total: 전체 반복 횟수
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [dim]Iteration {current}/{total}[/dim]")

    def show_progress(self, completed: int, total: int) -> None:
        """체크박스 진행률을 시각적 진행 바와 함께 표시 (타임스탬프 포함).

        Args:
            completed: 완료된 체크박스 개수
            total: 전체 체크박스 개수
        """
        if total == 0:
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        percentage = int((completed / total) * 100)
        remaining = total - completed

        bar_length = 20
        filled = int((completed / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        self.write(
            f"[dim]{timestamp}[/dim] [cyan]📋 진행률:[/cyan] {bar} "
            f"[bold]{completed}/{total}[/bold] ({percentage}%) "
            f"[dim]| 남은 작업: {remaining}개[/dim]"
        )
