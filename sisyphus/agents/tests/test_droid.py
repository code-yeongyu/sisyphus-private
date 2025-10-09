"""Tests for DroidAgent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sisyphus.agents.base import Agent
from sisyphus.agents.droid import DroidAgent
from sisyphus.utils.errors import AgentNotFoundError, ProcessTimeoutError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = [pytest.mark.anyio]


async def test_agent_protocol_validation() -> None:
    # given
    agent = DroidAgent()

    # when
    is_valid = isinstance(agent, Agent)  # type: ignore[arg-type]

    # then
    assert is_valid


async def test_supports_interactive_is_false() -> None:
    # given
    agent = DroidAgent()

    # when
    supports = agent.supports_interactive

    # then
    assert supports is False


async def test_initialize_finds_binary_in_path() -> None:
    # given
    agent = DroidAgent()

    # when
    with patch("shutil.which", return_value="/usr/local/bin/droid"):
        await agent.initialize()

    # then
    assert agent._binary_path == Path("/usr/local/bin/droid")


async def test_initialize_uses_binary_parameter() -> None:
    # given
    binary_path = Path("/custom/path/droid")
    agent = DroidAgent(binary=binary_path)

    # when
    with patch("pathlib.Path.exists", return_value=True):
        await agent.initialize()

    # then
    assert agent._binary_path == binary_path


async def test_initialize_uses_env_variable() -> None:
    # given
    agent = DroidAgent()

    # when
    with (
        patch("shutil.which", return_value=None),
        patch("os.getenv", return_value="/env/path/droid"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        await agent.initialize()

    # then
    assert agent._binary_path == Path("/env/path/droid")


async def test_initialize_binary_not_found() -> None:
    # given
    agent = DroidAgent()

    # when/then
    with (
        patch("shutil.which", return_value=None),
        patch("os.getenv", return_value=None),
        pytest.raises(AgentNotFoundError, match="Droid binary not found"),
    ):
        await agent.initialize()


async def test_initialize_binary_parameter_not_exists() -> None:
    # given
    binary_path = Path("/nonexistent/droid")
    agent = DroidAgent(binary=binary_path)

    # when/then
    with (
        patch("pathlib.Path.exists", return_value=False),
        pytest.raises(AgentNotFoundError, match="Droid binary not found at:"),
    ):
        await agent.initialize()


async def test_start_session_generates_uuid() -> None:
    # given
    agent = DroidAgent()
    agent._binary_path = Path("/usr/local/bin/droid")
    mock_process = MagicMock()

    # when
    with patch(
        "sisyphus.utils.process.ProcessManager.run_with_timeout",
        return_value=mock_process,
    ):
        session_id = await agent.start_session()

    # then
    assert session_id is not None
    assert len(session_id) == 36
    assert agent._session_id == session_id


async def test_start_session_uses_provided_session_id() -> None:
    # given
    agent = DroidAgent()
    agent._binary_path = Path("/usr/local/bin/droid")
    provided_session_id = "12345678-1234-1234-1234-123456789abc"
    mock_process = MagicMock()

    # when
    with patch(
        "sisyphus.utils.process.ProcessManager.run_with_timeout",
        return_value=mock_process,
    ):
        session_id = await agent.start_session(provided_session_id)

    # then
    assert session_id == provided_session_id
    assert agent._session_id == provided_session_id


async def test_start_session_includes_autonomy_unsafe() -> None:
    # given
    agent = DroidAgent()
    agent._binary_path = Path("/usr/local/bin/droid")
    mock_process = MagicMock()
    captured_cmd = None

    async def capture_cmd(cmd: list[str], timeout_seconds: float) -> MagicMock:
        nonlocal captured_cmd
        captured_cmd = cmd
        return mock_process

    # when
    with patch(
        "sisyphus.utils.process.ProcessManager.run_with_timeout",
        side_effect=capture_cmd,
    ):
        await agent.start_session()

    # then
    assert captured_cmd is not None
    assert "--skip-permissions-unsafe" in captured_cmd


async def test_start_session_includes_model() -> None:
    # given
    agent = DroidAgent(model="claude-opus-4-1-20250805")
    agent._binary_path = Path("/usr/local/bin/droid")
    mock_process = MagicMock()
    captured_cmd = None

    async def capture_cmd(cmd: list[str], timeout_seconds: float) -> MagicMock:
        nonlocal captured_cmd
        captured_cmd = cmd
        return mock_process

    # when
    with patch(
        "sisyphus.utils.process.ProcessManager.run_with_timeout",
        side_effect=capture_cmd,
    ):
        await agent.start_session()

    # then
    assert captured_cmd is not None
    assert "--model" in captured_cmd
    assert "claude-opus-4-1-20250805" in captured_cmd


async def test_start_session_without_initialize_raises_error() -> None:
    # given
    agent = DroidAgent()

    # when/then
    with pytest.raises(RuntimeError, match="Binary not initialized"):
        await agent.start_session()


async def test_send_message() -> None:
    # given
    agent = DroidAgent()
    mock_stdin = AsyncMock()
    mock_process = MagicMock()
    mock_process.stdin = mock_stdin
    agent._process = mock_process

    # when
    await agent.send("Hello, Droid!")

    # then
    mock_stdin.send.assert_called_once()
    sent_data = mock_stdin.send.call_args[0][0]
    sent_json = json.loads(sent_data.decode("utf-8").strip())
    assert sent_json == {"role": "user", "content": "Hello, Droid!"}


async def test_send_without_process_raises_error() -> None:
    # given
    agent = DroidAgent()

    # when/then
    with pytest.raises(RuntimeError, match="Process not started"):
        await agent.send("test")


async def test_stream_messages() -> None:
    # given
    agent = DroidAgent()
    mock_process = MagicMock()
    agent._process = mock_process

    async def mock_parse_jsonl() -> AsyncIterator[dict[str, str]]:
        yield {"role": "assistant", "content": "Hello!", "model": "gpt-5"}
        yield {"role": "system", "content": "Task complete", "status": "done"}

    # when
    messages = []
    with patch(
        "sisyphus.utils.process.ProcessManager.parse_jsonl_stream",
        side_effect=lambda _: mock_parse_jsonl(),
    ):
        async for msg in agent.stream():
            messages.append(msg)

    # then
    assert len(messages) == 2
    assert messages[0].role == "assistant"
    assert messages[0].content == "Hello!"
    assert messages[0].metadata == {"model": "gpt-5"}
    assert messages[1].role == "system"
    assert messages[1].content == "Task complete"
    assert messages[1].metadata == {"status": "done"}


async def test_stream_without_process_raises_error() -> None:
    # given
    agent = DroidAgent()

    # when/then
    with pytest.raises(RuntimeError, match="Process not started"):
        async for _ in agent.stream():
            pass


async def test_close_terminates_process() -> None:
    # given
    agent = DroidAgent()
    mock_process = MagicMock()
    agent._process = mock_process

    # when
    with patch("sisyphus.utils.process.ProcessManager.terminate_gracefully") as mock_terminate:
        await agent.close()

    # then
    mock_terminate.assert_called_once_with(mock_process, timeout_seconds=5.0)
    assert agent._process is None


async def test_close_without_process() -> None:
    # given
    agent = DroidAgent()

    # when
    await agent.close()

    # then
    assert agent._process is None


async def test_timeout_handling() -> None:
    # given
    agent = DroidAgent()
    agent._binary_path = Path("/usr/local/bin/droid")

    # when/then
    with (
        patch(
            "sisyphus.utils.process.ProcessManager.run_with_timeout",
            side_effect=ProcessTimeoutError("Timeout"),
        ),
        pytest.raises(ProcessTimeoutError, match="Timeout"),
    ):
        await agent.start_session()
