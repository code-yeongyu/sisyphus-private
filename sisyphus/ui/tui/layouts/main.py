"""Main layout composition for TUI."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll

from sisyphus.ui.tui.components.chat_log import ChatLog
from sisyphus.ui.tui.components.input_bar import InputBar
from sisyphus.ui.tui.components.status_panel import StatusPanel


def compose_main_layout() -> ComposeResult:
    """Compose the main layout."""
    yield Container(
        VerticalScroll(
            ChatLog(),
            id="chat-scroll",
        ),
        Container(
            StatusPanel(),
            id="status-container",
        ),
    )
    yield InputBar()
