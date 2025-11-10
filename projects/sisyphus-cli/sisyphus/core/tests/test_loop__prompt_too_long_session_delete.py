"""Tests for ExecutionLoop PromptTooLongError session deletion."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sisyphus.core.loop import ExecutionLoop
from sisyphus.core.tests.test_loop import MockStatusManager
from sisyphus.core.session import SessionStore
from sisyphus.utils.errors import PromptTooLongError
from sisyphus.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


class MockAgentWithPromptError:
    """Mock agent that raises PromptTooLongError."""

    def __init__(self, fail_count: int = 1) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.closed = False
        self.fail_count = fail_count
        self.call_count = 0

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = "new-session-123"
        return self.session_id

    async def send(self, message: str) -> None:
        pass

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            self.call_count += 1
            if self.call_count <= self.fail_count:
                raise PromptTooLongError("Prompt exceeded maximum length")
            yield AgentMessage(role="assistant", content="Success after session reset")

        return _generator()

    async def close(self) -> None:
        self.closed = True


class MockUI:
    """Mock UI for testing."""

    def __init__(self) -> None:
        self.messages: list[AgentMessage] = []
        self.status_messages: list[str] = []

    async def initialize(self) -> None:
        pass

    async def show_message(self, message: AgentMessage, source: str = "execute") -> None:
        self.messages.append(message)

    async def show_status(self, status: str) -> None:
        self.status_messages.append(status)

    async def get_input(self) -> str | None:
        return None


async def test_execution_loop__if_prompt_too_long_error__deletes_session(tmp_path: Path) -> None:
    """Test that PromptTooLongError triggers session deletion."""
    # given
    session_dir = tmp_path / "sessions"
    session_store = SessionStore(base_dir=session_dir)

    await session_store.save_session("mockwithprompterror", "old-session-id", "default")

    agent = MockAgentWithPromptError(fail_count=1)
    ui = MockUI()
    logger_factory = MagicMock()
    logger_factory.create_logger.return_value = MagicMock()

    loop = ExecutionLoop(
        execute_agent=agent,
        verify_agent=None,
        ui=ui,
        session_store=session_store,
        logger_factory=logger_factory,
        task_validator=None,
    )

    # when
    await loop.run()

    # then
    sessions = await session_store.list_sessions()
    assert sessions["mockwithprompterror"]["default"]["session_id"] != "old-session-id"
    assert sessions["mockwithprompterror"]["default"]["session_id"] == "new-session-123"

    assert any("Session 'mockwithprompterror' cleared" in msg for msg in ui.status_messages)
    assert any("prompt length exceeded" in msg for msg in ui.status_messages)


async def test_execution_loop__if_prompt_too_long_error__starts_new_session(tmp_path: Path) -> None:
    """Test that after session deletion, new session is started."""
    # given
    session_dir = tmp_path / "sessions"
    session_store = SessionStore(base_dir=session_dir)

    await session_store.save_session("mockwithprompterror", "old-session-id", "default")

    agent = MockAgentWithPromptError(fail_count=1)
    ui = MockUI()
    logger_factory = MagicMock()
    logger_factory.create_logger.return_value = MagicMock()

    loop = ExecutionLoop(
        execute_agent=agent,
        verify_agent=None,
        ui=ui,
        session_store=session_store,
        logger_factory=logger_factory,
        task_validator=None,
    )

    # when
    await loop.run()

    # then
    assert agent.call_count == 2
    assert len(ui.messages) == 1
    assert ui.messages[0].content == "Success after session reset"
