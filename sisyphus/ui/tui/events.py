"""TUI custom events."""

from textual.message import Message


class InputReadyEvent(Message):
    """Notifies that user input is ready (Enter key pressed)."""


class AgentInterruptEvent(Message):
    """Agent interrupt request event."""


class AgentResumeEvent(Message):
    """Agent resume request event."""
