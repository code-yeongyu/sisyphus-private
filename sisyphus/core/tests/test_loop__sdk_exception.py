"""Tests for ExecutionLoop SDK Exception handling."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from sisyphus.core.loop import ExecutionLoop
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


async def test_execute_phase__if_sdk_runtime_error__deletes_session_and_retries() -> None:
    """Test that SDK RuntimeError deletes session and allows retry."""
    mock_agent = MagicMock(spec=["initialize", "start_session", "send", "stream", "close", "session_id"])
    mock_agent.initialize = AsyncMock()
    mock_agent.start_session = AsyncMock(return_value="session_123")
    mock_agent.send = AsyncMock()
    mock_agent.close = AsyncMock()
    mock_agent.session_id = "session_123"

    call_count = 0

    def create_mock_stream() -> AsyncIterator[AgentMessage]:
        async def mock_stream() -> AsyncIterator[AgentMessage]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Claude Agent SDK error: Command failed with exit code 1")
            yield AgentMessage(role="assistant", content="Success after retry", metadata={})

        return mock_stream()

    mock_agent.stream = create_mock_stream

    mock_ui = MagicMock(spec=["initialize", "show_message", "show_status", "get_input"])
    mock_ui.initialize = AsyncMock()
    mock_ui.show_message = AsyncMock()
    mock_ui.show_status = AsyncMock()
    mock_ui.get_input = AsyncMock(return_value=None)

    mock_session_store = MagicMock(spec=["get_session", "save_session", "delete_session"])
    mock_session_store.get_session = AsyncMock(return_value="invalid_session")
    mock_session_store.save_session = AsyncMock()
    mock_session_store.delete_session = AsyncMock()

    mock_prompt_resolver = MagicMock(spec=["resolve"])
    mock_prompt_resolver.resolve = AsyncMock(return_value="Test prompt")

    mock_logger_factory = MagicMock(spec=["create_logger"])
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger_factory.create_logger = MagicMock(return_value=mock_logger)

    loop = ExecutionLoop(
        execute_agent=mock_agent,
        ui=mock_ui,
        session_store=mock_session_store,
        prompt_resolver=mock_prompt_resolver,
        logger_factory=mock_logger_factory,
    )

    await loop.run(execute_prompt="Test prompt")

    assert call_count == 2
    mock_session_store.delete_session.assert_called_once()
    assert mock_logger.info.call_count >= 2


async def test_execute_phase__if_sdk_exception_3_times__exits_phase() -> None:
    """Test that 3 consecutive SDK exceptions cause execute phase to exit."""
    mock_agent = MagicMock(spec=["initialize", "start_session", "send", "stream", "close", "session_id"])
    mock_agent.initialize = AsyncMock()
    mock_agent.start_session = AsyncMock(return_value="session_123")
    mock_agent.send = AsyncMock()
    mock_agent.close = AsyncMock()
    mock_agent.session_id = "session_123"

    call_count = 0

    def create_mock_stream() -> AsyncIterator[AgentMessage]:
        async def mock_stream() -> AsyncIterator[AgentMessage]:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Claude Agent SDK error: Command failed with exit code 1")
            yield  # type: ignore[unreachable]

        return mock_stream()

    mock_agent.stream = create_mock_stream

    mock_ui = MagicMock(spec=["initialize", "show_message", "show_status", "get_input"])
    mock_ui.initialize = AsyncMock()
    mock_ui.show_message = AsyncMock()
    mock_ui.show_status = AsyncMock()
    mock_ui.get_input = AsyncMock(return_value=None)

    mock_session_store = MagicMock(spec=["get_session", "save_session", "delete_session"])
    mock_session_store.get_session = AsyncMock(return_value=None)
    mock_session_store.save_session = AsyncMock()
    mock_session_store.delete_session = AsyncMock()

    mock_prompt_resolver = MagicMock(spec=["resolve"])
    mock_prompt_resolver.resolve = AsyncMock(return_value="Test prompt")

    mock_logger_factory = MagicMock(spec=["create_logger"])
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger_factory.create_logger = MagicMock(return_value=mock_logger)

    loop = ExecutionLoop(
        execute_agent=mock_agent,
        ui=mock_ui,
        session_store=mock_session_store,
        prompt_resolver=mock_prompt_resolver,
        logger_factory=mock_logger_factory,
    )

    await loop.run(execute_prompt="Test prompt")

    assert call_count == 3
    assert mock_session_store.delete_session.call_count == 3
    error_calls = [call for call in mock_logger.error.call_args_list if "SDK error" in str(call)]
    assert len(error_calls) >= 3
