"""Tests for ExecutionLoop feedback injection to execute phase."""

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


async def test_execute__if_no_feedback_history__uses_original_extra() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.all_complete = True

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
    await loop._run_unified_mode(
        execute_prompt="Do the task",
        execute_extra="Original extra content",
        verify_prompt=None,
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 1
    sent_prompt = execute_agent.sent_messages[0]
    assert "Original extra content" in sent_prompt
    assert "Architect Feedback" not in sent_prompt


async def test_execute__if_feedback_history_exists__appends_feedback_section() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()

    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Please fix the bug", metadata={}),
        AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [True, True]

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
    await loop._run_unified_mode(
        execute_prompt="Do the task",
        execute_extra="Original extra",
        verify_prompt=None,
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 2

    first_execution = execute_agent.sent_messages[0]
    assert "Architect Feedback" not in first_execution

    second_execution = execute_agent.sent_messages[1]
    assert "Original extra" in second_execution
    assert "🔍 Architect Feedback from Previous Iterations" in second_execution
    assert "<architect-feedback-history>" in second_execution
    assert '<feedback iteration="1">' in second_execution
    assert "Please fix the bug" in second_execution
    assert "**CRITICAL**: Address ALL issues" in second_execution


async def test_execute__if_multiple_feedbacks__includes_all_with_correct_numbering() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()

    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="First feedback", metadata={}),
        AgentMessage(role="assistant", content="Second feedback", metadata={}),
        AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [True, True, True]

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
    await loop._run_unified_mode(
        execute_prompt="Do the task",
        execute_extra=None,
        verify_prompt=None,
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 3

    third_execution = execute_agent.sent_messages[2]
    assert '<feedback iteration="1">' in third_execution
    assert "First feedback" in third_execution
    assert '<feedback iteration="2">' in third_execution
    assert "Second feedback" in third_execution

    first_idx = third_execution.index('<feedback iteration="1">')
    second_idx = third_execution.index('<feedback iteration="2">')
    assert first_idx < second_idx


class MockAgent:
    """Mock agent for testing."""

    def __init__(self) -> None:
        self.supports_interactive = False
        self.initialized = False
        self.session_id: str | None = None
        self.sent_messages: list[str] = []
        self.closed = False
        self.messages_to_return: list[AgentMessage] = []
        self.message_index = 0

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = f"session-{len(self.sent_messages)}"
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            if self.message_index < len(self.messages_to_return):
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
        self.all_complete = False
        self.completion_sequence: list[bool] = []
        self.call_count = 0

    def read_content(self) -> str:
        return "mock content"

    def check_all_goals_accomplished(self, content: str) -> bool:
        if self.completion_sequence:
            result = self.completion_sequence[min(self.call_count, len(self.completion_sequence) - 1)]
            return result
        return self.all_complete

    def check_all_checkboxes_completed(self, content: str) -> bool:
        result = self.check_all_goals_accomplished(content)
        self.call_count += 1
        return result

    def extract_uncompleted_checkboxes(self, content: str) -> list[str]:
        return []

    def count_total_checkboxes(self, content: str) -> int:
        return 1

    def count_completed_checkboxes(self, content: str) -> int:
        return 1 if self.all_complete else 0
