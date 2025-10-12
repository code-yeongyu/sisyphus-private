"""Tests for ExecutionLoop._run_unified_mode flow control."""

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


async def test_unified__if_task_incomplete__skips_verify_and_retries_execute() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Execute iteration 1", metadata={}),
        AgentMessage(role="assistant", content="Execute iteration 2", metadata={}),
    ]

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Verify feedback\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    task_validator = MockTaskValidator()
    task_validator.check_results = [
        (False, False),
        (True, True),
    ]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 2
    assert len(execute_agent.sent_messages) == 2
    assert len(verify_agent.sent_messages) == 1


async def test_unified__if_task_complete_and_fully_done__exits_loop() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Task completed", metadata={}),
    ]

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Great!\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    task_validator = MockTaskValidator()
    task_validator.check_results = [(True, True)]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 1
    assert len(verify_agent.sent_messages) == 1
    assert any("FULLY_DONE" in status for status in ui.statuses)


async def test_unified__if_task_complete_but_not_fully_done__continues_with_feedback() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Execute iteration 1", metadata={}),
        AgentMessage(role="assistant", content="Execute iteration 2", metadata={}),
    ]

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Needs improvement", metadata={}),
        AgentMessage(role="assistant", content="Better! FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()

    task_validator = MockTaskValidator()
    task_validator.check_results = [
        (True, True),
        (True, True),
    ]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        prompt_resolver=prompt_resolver,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 2
    assert len(execute_agent.sent_messages) == 2
    assert len(verify_agent.sent_messages) == 2
    assert any("feedback received" in status.lower() for status in ui.statuses)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.messages_to_return: list[AgentMessage] = []
        self.stream_call_count = 0

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
        call_index = self.stream_call_count
        self.stream_call_count += 1

        async def _generator() -> AsyncIterator[AgentMessage]:
            if call_index < len(self.messages_to_return):
                yield self.messages_to_return[call_index]

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


class MockTaskValidator:
    """Mock task validator for testing."""

    def __init__(self) -> None:
        self.check_results: list[tuple[bool, bool]] = []
        self.check_call_count = 0

    def read_content(self) -> str:
        return "mock content"

    def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        if self.check_call_count < len(self.check_results):
            return self.check_results[self.check_call_count][0]
        return True

    def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        result_index = self.check_call_count
        self.check_call_count += 1
        if result_index < len(self.check_results):
            return self.check_results[result_index][1]
        return True

    def extract_uncompleted_checkboxes(self, content: str | None = None) -> list[str]:
        return ["Task 1"]

    def count_total_checkboxes(self, content: str | None = None) -> int:
        return 10

    def count_completed_checkboxes(self, content: str | None = None) -> int:
        return 8
