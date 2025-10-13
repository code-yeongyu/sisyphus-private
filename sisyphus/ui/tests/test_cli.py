from __future__ import annotations

from unittest.mock import patch

import pytest
from rich.console import Console
from rich.markdown import Markdown

from sisyphus.ui.base import UIProtocol
from sisyphus.ui.cli import CLI
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


async def test_cli_protocol_compliance() -> None:
    # given
    cli = CLI()

    # when/then
    assert isinstance(cli, UIProtocol)


async def test_cli_initialize() -> None:
    # given
    cli = CLI()

    # when
    await cli.initialize()

    # then
    assert cli._initialized is True


async def test_cli_show_message_execute_source() -> None:
    # given
    cli = CLI()
    message = AgentMessage(role="assistant", content="Test message")

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_message(message, "execute")

    # then
    assert mock_print.call_count == 2
    first_call = mock_print.call_args_list[0]
    assert "[yellow]EXECUTE:[/yellow]" in str(first_call)
    assert first_call[1]["end"] == " "


async def test_cli_show_message_verify_source() -> None:
    # given
    cli = CLI()
    message = AgentMessage(role="assistant", content="Test message")

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_message(message, "verify")

    # then
    assert mock_print.call_count == 2
    first_call = mock_print.call_args_list[0]
    assert "[cyan]VERIFY:[/cyan]" in str(first_call)


async def test_cli_show_message_unknown_source() -> None:
    # given
    cli = CLI()
    message = AgentMessage(role="assistant", content="Test message")

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_message(message, "unknown")

    # then
    assert mock_print.call_count == 2
    first_call = mock_print.call_args_list[0]
    assert "[white]UNKNOWN:[/white]" in str(first_call)


async def test_cli_show_message_with_markdown() -> None:
    # given
    cli = CLI()
    markdown_content = "# Heading\n\n**bold** and *italic*"
    message = AgentMessage(role="assistant", content=markdown_content)

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_message(message, "execute")

    # then
    assert mock_print.call_count == 2
    second_call = mock_print.call_args_list[1]

    assert isinstance(second_call[0][0], Markdown)


async def test_cli_show_message_empty_content() -> None:
    # given
    cli = CLI()
    message = AgentMessage(role="assistant", content="")

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_message(message, "execute")

    # then
    assert mock_print.call_count == 2
    second_call = mock_print.call_args_list[1]
    assert second_call[0] == ()


async def test_cli_show_status() -> None:
    # given
    cli = CLI()
    status_text = "Processing task 1/5"

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_status(status_text)

    # then
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert "[blue]" in call_args
    assert status_text in call_args


async def test_cli_get_input_returns_none() -> None:
    # given
    cli = CLI()

    # when
    result = await cli.get_input()

    # then
    assert result is None


async def test_cli_lifecycle() -> None:
    # given
    cli = CLI()

    # when
    await cli.initialize()

    # then
    assert cli._initialized is True


async def test_cli_full_lifecycle() -> None:
    # given
    cli = CLI()

    # when/then: initialize
    await cli.initialize()
    assert cli._initialized is True

    # when/then: show messages
    msg1 = AgentMessage(role="user", content="Hello")
    with patch.object(cli.console, "print"):
        await cli.show_message(msg1, "execute")

    msg2 = AgentMessage(role="assistant", content="World")
    with patch.object(cli.console, "print"):
        await cli.show_message(msg2, "verify")

    # when/then: show status
    with patch.object(cli.console, "print"):
        await cli.show_status("Status update")

    # when/then: get input
    user_input = await cli.get_input()
    assert user_input is None

    # then: CLI remains initialized (no close method)
    assert cli._initialized is True


async def test_cli_multiple_messages_sequence() -> None:
    # given
    cli = CLI()
    messages = [
        AgentMessage(role="user", content="Message 1"),
        AgentMessage(role="assistant", content="Message 2"),
        AgentMessage(role="user", content="Message 3"),
    ]

    # when
    with patch.object(cli.console, "print") as mock_print:
        for i, msg in enumerate(messages):
            source = "execute" if i % 2 == 0 else "verify"
            await cli.show_message(msg, source)

    # then
    assert mock_print.call_count == len(messages) * 2


async def test_cli_console_instance_creation() -> None:
    # given/when
    cli = CLI()

    # then

    assert isinstance(cli.console, Console)


async def test_cli_message_with_metadata() -> None:
    # given
    cli = CLI()
    message = AgentMessage(
        role="assistant",
        content="Test content",
        metadata={"session_id": "test-123", "timestamp": "2025-10-09"},
    )

    # when
    with patch.object(cli.console, "print") as mock_print:
        await cli.show_message(message, "execute")

    # then
    assert mock_print.call_count == 2
