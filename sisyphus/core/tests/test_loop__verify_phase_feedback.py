"""Tests for ExecutionLoop._verify_phase feedback collection."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from sisyphus.core.loop import ExecutionLoop
from sisyphus.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


async def test_verify_phase__if_fully_done_true_in_message__returns_true_and_feedback() -> None:
    # given
    mock_verify_agent = MockAgent()
    mock_verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Good work!\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=MockAgent(),  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=mock_verify_agent,  # type: ignore[arg-type]
    )

    # when
    feedback, fully_done = await loop._verify_phase("test prompt", None)

    # then
    assert fully_done is True
    assert "Good work!" in feedback
    assert "FULLY_DONE = TRUE" in feedback


async def test_verify_phase__if_fully_done_false__returns_false_and_feedback() -> None:
    # given
    mock_verify_agent = MockAgent()
    mock_verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Needs improvement", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=MockAgent(),  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=mock_verify_agent,  # type: ignore[arg-type]
    )

    # when
    feedback, fully_done = await loop._verify_phase("test prompt", None)

    # then
    assert fully_done is False
    assert "Needs improvement" in feedback


async def test_verify_phase__if_multiple_messages__concatenates_with_newlines() -> None:
    # given
    mock_verify_agent = MockAgent()
    mock_verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="First message", metadata={}),
        AgentMessage(role="assistant", content="Second message", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=MockAgent(),  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=mock_verify_agent,  # type: ignore[arg-type]
    )

    # when
    feedback, fully_done = await loop._verify_phase("test prompt", None)

    # then
    assert "First message\n\nSecond message" == feedback


async def test_verify_phase__if_no_assistant_messages__returns_empty_string() -> None:
    # given
    mock_verify_agent = MockAgent()
    mock_verify_agent.messages_to_return = [
        AgentMessage(role="system", content="System message", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=MockAgent(),  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=mock_verify_agent,  # type: ignore[arg-type]
    )

    # when
    feedback, fully_done = await loop._verify_phase("test prompt", None)

    # then
    assert feedback == ""
    assert fully_done is False


class MockAgent:
    """Mock agent for testing."""

    def __init__(self) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.messages_to_return: list[AgentMessage] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = "new-session-123"
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            for msg in self.messages_to_return:
                yield msg

        return _generator()

    async def close(self) -> None:
        self.closed = True


class MockUI:
    """Mock UI for testing."""

    def __init__(self) -> None:
        self.initialized = False
        self.messages: list[tuple[AgentMessage, str]] = []
        self.statuses: list[str] = []
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        self.messages.append((message, source))

    async def show_status(self, status: str) -> None:
        self.statuses.append(status)

    async def get_input(self) -> str | None:
        return None

    async def close(self) -> None:
        self.closed = True


class MockSessionStore:
    """Mock session store for testing."""

    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}

    async def get_session(self, agent_type: str) -> str | None:
        return self.sessions.get(agent_type)

    async def save_session(self, agent_type: str, session_id: str) -> None:
        self.sessions[agent_type] = session_id

    async def delete_session(self, agent_type: str) -> None:
        if agent_type in self.sessions:
            del self.sessions[agent_type]

    async def list_sessions(self) -> dict[str, dict[str, str]]:
        return {k: {"session_id": v} for k, v in self.sessions.items()}


class MockPromptResolver:
    """Mock prompt resolver for testing."""

    async def resolve(self, prompt: str, extra: str | None = None) -> str:
        if extra:
            return f"{prompt}\n\n{extra}"
        return prompt


class MockLoggerFactory:
    """Mock logger factory for testing."""

    @staticmethod
    def create_logger(agent_type: str, session_id: str | None = None, log_dir: Path = Path("./logs")) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.warning = MagicMock()
        return logger
