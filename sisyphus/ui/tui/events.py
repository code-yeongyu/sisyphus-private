"""TUI custom events."""

from textual.message import Message


class InputReadyEvent(Message):
    """사용자가 Enter를 눌러 입력이 준비되었음을 알림."""


class AgentInterruptEvent(Message):
    """에이전트 중단 요청 이벤트."""


class AgentResumeEvent(Message):
    """에이전트 재개 요청 이벤트."""
