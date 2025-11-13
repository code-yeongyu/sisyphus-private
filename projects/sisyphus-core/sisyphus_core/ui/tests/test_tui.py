"""TUI tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from sisyphus.ui.base import UIProtocol
from sisyphus.ui.tui.app import TUI, ShowAgentMessage, UpdateStatusMessage
from sisyphus.ui.tui.components.input_bar import InputBar
from sisyphus.ui.tui.components.status_panel import StatusPanel
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio()]


async def test_tui_protocol_compliance() -> None:
    """Verifies that TUI satisfies UIProtocol."""
    # given
    tui = TUI()

    # when / then
    assert isinstance(tui, UIProtocol)


async def test_tui_initialize() -> None:
    """Tests TUI initialization."""
    # given
    tui = TUI()
    assert tui._initialized is False

    # when
    await tui.initialize()

    # then
    assert tui._initialized is True


async def test_tui_show_message_execute() -> None:
    """Tests Execute message display."""
    # given
    tui = TUI()
    tui.ready_event.set()
    message = AgentMessage(role="assistant", content="Test execute content")

    # when
    with patch.object(tui, "post_message") as mock_post:
        await tui.show_message(message, "execute")

    # then
    mock_post.assert_called_once()
    posted_msg = mock_post.call_args[0][0]
    assert isinstance(posted_msg, ShowAgentMessage)
    assert posted_msg.message.content == "Test execute content"
    assert posted_msg.source == "execute"


async def test_tui_show_message_verify() -> None:
    """Tests Verify message display."""
    # given
    tui = TUI()
    tui.ready_event.set()
    message = AgentMessage(role="assistant", content="Test verify content")

    # when
    with patch.object(tui, "post_message") as mock_post:
        await tui.show_message(message, "verify")

    # then
    mock_post.assert_called_once()
    posted_msg = mock_post.call_args[0][0]
    assert isinstance(posted_msg, ShowAgentMessage)
    assert posted_msg.message.content == "Test verify content"
    assert posted_msg.source == "verify"


async def test_tui_show_message_with_metadata() -> None:
    """Tests message display with metadata."""
    # given
    tui = TUI()
    tui.ready_event.set()
    message = AgentMessage(
        role="assistant",
        content="Test content with metadata",
        metadata={"session_id": "test-123", "timestamp": "2025-10-09"},
    )

    # when
    with patch.object(tui, "post_message") as mock_post:
        await tui.show_message(message, "execute")

    # then
    mock_post.assert_called_once()
    posted_msg = mock_post.call_args[0][0]
    assert isinstance(posted_msg, ShowAgentMessage)
    assert posted_msg.message.content == "Test content with metadata"


async def test_tui_show_status() -> None:
    """Tests status display."""
    # given
    tui = TUI()
    tui.ready_event.set()
    status_text = "Processing task 1/5"

    # when
    with patch.object(tui, "post_message") as mock_post:
        await tui.show_status(status_text)

    # then
    mock_post.assert_called_once()

    posted_msg = mock_post.call_args[0][0]
    assert isinstance(posted_msg, UpdateStatusMessage)
    assert posted_msg.status == status_text


async def test_tui_get_input_from_queue() -> None:
    """Tests getting input from message queue."""
    # given
    tui = TUI()

    mock_input_bar = MagicMock(spec=InputBar)
    mock_input_bar.get_and_clear_queue.return_value = "Test user input"

    # when
    with patch.object(tui, "query_one", return_value=mock_input_bar):
        result = await tui.get_input()

    # then
    assert result == "Test user input"


async def test_tui_components_separated() -> None:
    """Verifies that components are separated."""
    # given
    tui = TUI()

    # when
    composition = list(tui.compose())

    # then
    # Verify that compose() yields layout
    assert len(composition) > 0


async def test_tui_ctrl_c_once() -> None:
    """Shows warning when Ctrl+C is pressed once."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # when
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    # then
    assert tui.ctrl_c_count == 1
    assert tui.last_ctrl_c_time is not None
    mock_status_panel.update_status.assert_called_once_with("⚠️ Press Ctrl+C once more to exit")


async def test_tui_ctrl_c_twice() -> None:
    """Exits when Ctrl+C is pressed twice (within 1 second)."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # First Ctrl+C
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    assert tui.ctrl_c_count == 1

    # when: Second Ctrl+C (within 1 second)
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        with patch.object(tui, "exit") as mock_exit:
            await tui._handle_interrupt()

    # then
    assert tui.ctrl_c_count == 2
    assert tui.shutdown_event.is_set()
    mock_exit.assert_called_once()


async def test_tui_ctrl_c_reset() -> None:
    """Resets counter when more than 1 second passes after Ctrl+C."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # First Ctrl+C
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    assert tui.ctrl_c_count == 1
    first_time = tui.last_ctrl_c_time

    # when: Ctrl+C after more than 1 second
    # Set last_ctrl_c_time to more than 1 second ago
    tui.last_ctrl_c_time = datetime.now() - timedelta(seconds=2)

    with patch.object(tui, "query_one", return_value=mock_status_panel):
        await tui._handle_interrupt()

    # then
    # Counter is reset back to 1
    assert tui.ctrl_c_count == 1
    assert tui.last_ctrl_c_time is not None
    assert tui.last_ctrl_c_time != first_time


async def test_tui_safe_shutdown() -> None:
    """Tests safe shutdown procedure."""
    # given
    tui = TUI()
    mock_status_panel = MagicMock(spec=StatusPanel)

    # when
    with patch.object(tui, "query_one", return_value=mock_status_panel):
        with patch.object(tui, "exit") as mock_exit:
            await tui._safe_shutdown()

    # then
    assert tui.shutdown_event.is_set()
    mock_exit.assert_called_once()
    mock_status_panel.update_status.assert_called_once_with("🔄 Shutting down...")


async def test_tui_full_lifecycle() -> None:
    """Tests full lifecycle."""
    # given
    tui = TUI()

    # when/then: initialize
    await tui.initialize()
    assert tui._initialized is True

    # when/then: on_mount
    await tui.on_mount()
    assert tui.ready_event.is_set()

    # when/then: show message
    with patch.object(tui, "post_message") as mock_post:
        msg1 = AgentMessage(role="user", content="Execute message")
        await tui.show_message(msg1, "execute")
    assert mock_post.called

    # when/then: show status
    with patch.object(tui, "post_message") as mock_post_status:
        await tui.show_status("Status update")
    assert mock_post_status.called

    # when/then: get input
    mock_input_bar = MagicMock(spec=InputBar)
    mock_input_bar.get_and_clear_queue.return_value = "Test input"
    with patch.object(tui, "query_one", return_value=mock_input_bar):
        user_input = await tui.get_input()
    assert user_input == "Test input"


async def test_tui_multiple_messages_sequence() -> None:
    """Tests sequential display of multiple messages."""
    # given
    tui = TUI()
    tui.ready_event.set()
    messages = [
        (AgentMessage(role="user", content="Message 1"), "execute"),
        (AgentMessage(role="assistant", content="Message 2"), "verify"),
        (AgentMessage(role="user", content="Message 3"), "execute"),
    ]

    # when
    with patch.object(tui, "post_message") as mock_post:
        for msg, source in messages:
            await tui.show_message(msg, source)

    # then
    assert mock_post.call_count == 3


async def test_tui_empty_message_content() -> None:
    """Tests handling of empty message content."""
    # given
    tui = TUI()
    tui.ready_event.set()
    message = AgentMessage(role="assistant", content="")

    # when
    with patch.object(tui, "post_message") as mock_post:
        await tui.show_message(message, "execute")

    # then
    mock_post.assert_called_once()
    posted_msg = mock_post.call_args[0][0]
    assert isinstance(posted_msg, ShowAgentMessage)
    assert posted_msg.message.content == ""
