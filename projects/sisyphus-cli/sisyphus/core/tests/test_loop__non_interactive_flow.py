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
    logger_factory = MockLoggerFactory()

    task_validator = MockTaskValidator()
    task_validator.check_results = [
        (False, False),  # Initial check
        (False, False),  # Skip_execute check (iteration==1)
        (False, False),  # After first execute (incomplete, retry)
        (True, True),  # After second execute (complete, verify)
    ]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )
    loop._current_plan_id = "default"

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 4
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
    logger_factory = MockLoggerFactory()

    task_validator = MockTaskValidator()
    task_validator.check_results = [(True, True)]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )
    loop._current_plan_id = "default"

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 3
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
    verify_agent.response_sequence = [
        [AgentMessage(role="assistant", content="Needs improvement\nFULLY_DONE = FALSE", metadata={})],
        [AgentMessage(role="assistant", content="Better! FULLY_DONE = TRUE", metadata={})],
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    task_validator = MockTaskValidator()
    task_validator.check_results = [
        (False, False),  # Initial check
        (False, False),  # Skip_execute check (iteration==1)
        (True, True),  # After first execute -> verify
        (True, True),  # After second execute -> verify (with feedback)
    ]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )
    loop._current_plan_id = "default"

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 4
    assert len(execute_agent.sent_messages) == 2
    assert len(verify_agent.sent_messages) == 2


class MockAgent:
    """Mock agent for testing."""

    def __init__(self) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.messages_to_return: list[AgentMessage] = []
        self.response_sequence: list[list[AgentMessage]] = []
        self.message_index = 0
        self.session_count = 0

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = f"session-{self.session_count}"
            self.session_count += 1
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            if self.response_sequence:
                session_idx = self.session_count - 1
                if 0 <= session_idx < len(self.response_sequence):
                    for msg in self.response_sequence[session_idx]:
                        yield msg
            elif self.message_index < len(self.messages_to_return):
                yield self.messages_to_return[self.message_index]
                self.message_index += 1

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

    async def get_session(self, agent_type: str, plan_id: str) -> str | None:
        return self.sessions.get(agent_type)

    async def save_session(self, agent_type: str, session_id: str, plan_id: str) -> None:
        self.sessions[agent_type] = session_id

    async def delete_session(self, agent_type: str, plan_id: str | None = None) -> None:
        if agent_type in self.sessions:
            del self.sessions[agent_type]

    async def list_sessions(self) -> dict[str, dict[str, str]]:
        return {k: {"session_id": v} for k, v in self.sessions.items()}


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
        self.todolist_path = None

    def read_content(self) -> str:
        return "mock content"

    async def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        if self.check_call_count < len(self.check_results):
            return self.check_results[self.check_call_count][0]
        return True

    async def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
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
