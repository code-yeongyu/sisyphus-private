"""StatusPanel component for TUI."""

from datetime import datetime

from textual.widgets import RichLog


class StatusPanel(RichLog):
    """Status panel widget.

    Inherits RichLog widget to display task status and iteration progress.
    """

    def __init__(self) -> None:
        """Initialize StatusPanel widget.

        Enables Rich markup, syntax highlighting, and auto-scroll features.
        """
        super().__init__(
            id="status-panel",
            highlight=True,
            markup=True,
            auto_scroll=True,
        )

    def update_status(self, status: str) -> None:
        """Update status (with timestamp).

        Args:
            status: Status message to display
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [blue]{status}[/blue]")

    def show_iteration(self, current: int, total: int) -> None:
        """Display iteration progress (with timestamp).

        Args:
            current: Current iteration number
            total: Total iteration count
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.write(f"[dim]{timestamp}[/dim] [dim]Iteration {current}/{total}[/dim]")

    def show_progress(self, completed: int, total: int) -> None:
        """Display checkbox progress with visual progress bar (with timestamp).

        Args:
            completed: Number of completed checkboxes
            total: Total number of checkboxes
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
            f"[dim]{timestamp}[/dim] [cyan]📋 Progress:[/cyan] {bar} "
            f"[bold]{completed}/{total}[/bold] ({percentage}%) "
            f"[dim]| Remaining: {remaining}[/dim]"
        )
