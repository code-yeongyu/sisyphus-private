"""Tests for ClaudeAgent."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock

from sisyphus.agents.base import Agent
from sisyphus.agents.claude import ClaudeAgent
from sisyphus.utils.errors import SessionResumeError
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


@pytest.fixture()
def mock_sdk_client() -> MagicMock:
    """Create a mock ClaudeSDKClient."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.query = AsyncMock()
    client.receive_response = AsyncMock()
    return client


@pytest.fixture()
def mock_sdk_options() -> MagicMock:
    """Create a mock ClaudeAgentOptions."""
    return MagicMock()


async def test_agent_protocol_validation() -> None:
    """Test that ClaudeAgent satisfies Agent Protocol."""
    # given
    agent = ClaudeAgent()

    # when/then
    assert isinstance(agent, Agent)
    assert agent.supports_interactive is True


async def test_initialize_creates_client(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test that initialize() creates SDK client with correct options."""
    # given
    agent = ClaudeAgent(model="claude-sonnet-4-5-20250929")

    # when
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options) as mock_options_cls:
            await agent.initialize()

    # then
    assert agent._client == mock_sdk_client
    assert agent._options == mock_sdk_options
    mock_options_cls.assert_called_once()
    call_kwargs = mock_options_cls.call_args[1]
    assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"
    assert call_kwargs["permission_mode"] == "bypassPermissions"
    assert call_kwargs["include_partial_messages"] is True


async def test_initialize_with_sdk_options_override(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test that sdk_options override defaults."""
    # given
    custom_options = {"permission_mode": "custom", "extra_option": "value"}
    agent = ClaudeAgent(sdk_options=custom_options)

    # when
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options) as mock_options_cls:
            await agent.initialize()

    # then
    call_kwargs = mock_options_cls.call_args[1]
    assert call_kwargs["permission_mode"] == "custom"
    assert call_kwargs["extra_option"] == "value"


async def test_start_session_new(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test starting a new session."""
    # given
    agent = ClaudeAgent()
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()

    # when
    session_id = await agent.start_session()

    # then
    assert session_id == ""
    assert agent._connected is True
    mock_sdk_client.connect.assert_called_once()


async def test_start_session_resume(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test resuming an existing session."""
    # given
    agent = ClaudeAgent()
    resume_session_id = "test-session-123"

    # when
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options) as mock_options_cls:
            session_id = await agent.start_session(resume_session_id)

    # then
    assert session_id == resume_session_id
    assert agent._connected is True
    mock_sdk_client.connect.assert_called_once()
    call_kwargs = mock_options_cls.call_args[1]
    assert call_kwargs["resume"] == resume_session_id


async def test_start_session_resume_failure(mock_sdk_client: MagicMock) -> None:
    """Test session resume failure raises SessionResumeError."""
    # given
    agent = ClaudeAgent()
    mock_sdk_client.connect.side_effect = Exception("Session not found")

    # when/then
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions"):
            with pytest.raises(SessionResumeError, match="Failed to resume session"):
                await agent.start_session("invalid-session")


async def test_send_message(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test sending a message."""
    # given
    agent = ClaudeAgent()
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    await agent.send("Hello Claude")

    # then
    mock_sdk_client.query.assert_called_once_with("Hello Claude")


async def test_send_without_connection_raises_error() -> None:
    """Test that send() raises error when not connected."""
    # given
    agent = ClaudeAgent()

    # when/then
    with pytest.raises(RuntimeError, match="Client not connected"):
        await agent.send("Hello")


async def test_stream_assistant_message(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test streaming assistant messages."""
    # given
    agent = ClaudeAgent()

    text_block = TextBlock(text="Hello from Claude")
    assistant_msg = MagicMock(spec=AssistantMessage)
    assistant_msg.content = [text_block]
    assistant_msg.model = "claude-sonnet-4-5"

    async def mock_receive() -> AsyncIterator[MagicMock]:
        yield assistant_msg

    mock_sdk_client.receive_response = mock_receive

    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert isinstance(messages[0], AgentMessage)
    assert messages[0].role == "assistant"
    assert messages[0].content == "Hello from Claude"
    assert messages[0].metadata["model"] == "claude-sonnet-4-5"


async def test_stream_system_message(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test streaming system messages."""
    # given
    agent = ClaudeAgent()

    system_msg = MagicMock(spec=SystemMessage)
    system_msg.subtype = "init"
    system_msg.data = {"session_id": "new-session-123"}

    async def mock_receive() -> AsyncIterator[MagicMock]:
        yield system_msg

    mock_sdk_client.receive_response = mock_receive

    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert messages[0].role == "system"
    assert agent._session_id == "new-session-123"


async def test_stream_result_message(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test streaming result messages."""
    # given
    agent = ClaudeAgent()

    result_msg = MagicMock(spec=ResultMessage)
    result_msg.session_id = "session-123"
    result_msg.duration_ms = 1000
    result_msg.num_turns = 5
    result_msg.is_error = False
    result_msg.result = None

    async def mock_receive() -> AsyncIterator[MagicMock]:
        yield result_msg

    mock_sdk_client.receive_response = mock_receive

    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    messages = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1
    assert messages[0].role == "system"
    assert messages[0].metadata["session_id"] == "session-123"
    assert messages[0].metadata["duration_ms"] == 1000
    assert messages[0].metadata["num_turns"] == 5
    assert messages[0].metadata["is_error"] is False


async def test_stream_without_connection_raises_error() -> None:
    """Test that stream() raises error when not connected."""
    # given
    agent = ClaudeAgent()

    # when/then
    with pytest.raises(RuntimeError, match="Client not connected"):
        async for _ in agent.stream():
            pass


async def test_close(mock_sdk_client: MagicMock, mock_sdk_options: MagicMock) -> None:
    """Test closing the agent."""
    # given
    agent = ClaudeAgent()
    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    await agent.close()

    # then
    assert agent._connected is False
    mock_sdk_client.disconnect.assert_called_once()


async def test_close_when_not_connected() -> None:
    """Test that close() works even when not connected."""
    # given
    agent = ClaudeAgent()

    # when/then
    await agent.close()
