"""Tests for ClaudeAgent Prompt is too long error detection."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

from sisyphus.agents.claude import ClaudeAgent
from sisyphus.utils.errors import PromptTooLongError
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


async def test_claude__if_result_message_has_prompt_too_long_error__raises_prompt_too_long_error(
    mock_sdk_client: MagicMock,
    mock_sdk_options: MagicMock,
) -> None:
    """Test that stream() raises PromptTooLongError when ResultMessage indicates error."""
    # given
    agent = ClaudeAgent()

    result_msg = MagicMock(spec=ResultMessage)
    result_msg.session_id = "sess_456"
    result_msg.duration_ms = 100
    result_msg.num_turns = 1
    result_msg.is_error = True
    result_msg.result = "Error: Prompt is too long (max 200000 tokens)"

    async def mock_receive() -> AsyncIterator[MagicMock]:
        yield result_msg

    mock_sdk_client.receive_response = mock_receive

    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when/then
    with pytest.raises(PromptTooLongError, match="Prompt exceeded maximum length"):
        async for _ in agent.stream():
            pass


async def test_claude__if_assistant_message_contains_prompt_too_long_text__yields_normally(
    mock_sdk_client: MagicMock,
    mock_sdk_options: MagicMock,
) -> None:
    """Test that stream() yields normally when Assistant talks about 'Prompt is too long' (not an error)."""
    # given
    agent = ClaudeAgent()

    text_block = TextBlock(text="The error 'Prompt is too long' means your input exceeded the limit.")
    assistant_msg = MagicMock(spec=AssistantMessage)
    assistant_msg.content = [text_block]
    assistant_msg.model = "claude-sonnet-4-5"

    result_msg = MagicMock(spec=ResultMessage)
    result_msg.session_id = "sess_456"
    result_msg.duration_ms = 100
    result_msg.num_turns = 1
    result_msg.is_error = False
    result_msg.result = None

    async def mock_receive() -> AsyncIterator[MagicMock]:
        yield assistant_msg
        yield result_msg

    mock_sdk_client.receive_response = mock_receive

    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    messages: list[AgentMessage] = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 2  # AssistantMessage + ResultMessage
    assert messages[0].role == "assistant"
    assert "Prompt is too long" in messages[0].content  # Text is preserved, not treated as error


async def test_claude__if_result_message_is_error_without_prompt_too_long__does_not_raise_prompt_too_long_error(
    mock_sdk_client: MagicMock,
    mock_sdk_options: MagicMock,
) -> None:
    """Test that other errors in ResultMessage don't trigger PromptTooLongError."""
    # given
    agent = ClaudeAgent()

    result_msg = MagicMock(spec=ResultMessage)
    result_msg.session_id = "sess_456"
    result_msg.duration_ms = 100
    result_msg.num_turns = 1
    result_msg.is_error = True
    result_msg.result = "Some other error occurred"

    async def mock_receive() -> AsyncIterator[MagicMock]:
        yield result_msg

    mock_sdk_client.receive_response = mock_receive

    with patch("sisyphus.agents.claude.ClaudeSDKClient", return_value=mock_sdk_client):
        with patch("sisyphus.agents.claude.ClaudeAgentOptions", return_value=mock_sdk_options):
            await agent.initialize()
            await agent.start_session()

    # when
    messages: list[AgentMessage] = []
    async for msg in agent.stream():
        messages.append(msg)

    # then
    assert len(messages) == 1  # ResultMessage only
    assert messages[0].role == "system"
    assert messages[0].metadata["is_error"] is True
