"""TUI custom events."""

from textual.message import Message


class InputReadyEvent(Message):
    """사용자가 Enter를 눌러 입력이 준비되었음을 알림."""
