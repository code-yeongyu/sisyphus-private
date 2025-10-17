"""Integration tests for ExecutionLoop complete feedback loop."""

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


async def test_feedback_loop__scenario_1_immediate_success() -> None:
    """Scenario 1: Execute → Task complete → Verify FULLY_DONE → Exit."""
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Perfect! FULLY_DONE = TRUE", metadata={}),
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
        execute_prompt="Do the work",
        execute_extra=None,
        verify_prompt="Verify the work",
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 1
    assert len(verify_agent.sent_messages) == 1
    assert task_validator.call_count == 1


async def test_feedback_loop__scenario_2_task_incomplete_retry() -> None:
    """Scenario 2: Execute → Task incomplete → Execute retry → Task complete → Verify → Exit."""
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="All done! FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    prompt_resolver = MockPromptResolver()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [False, True]

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
        execute_prompt="Do the work",
        execute_extra=None,
        verify_prompt="Verify the work",
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 2
    assert len(verify_agent.sent_messages) == 1
    assert task_validator.call_count == 2


async def test_feedback_loop__scenario_3_verify_feedback_iteration() -> None:
    """Scenario 3: Multiple Verify feedback iterations → Accumulate → Final success."""
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="First feedback: needs improvement in A", metadata={}),
        AgentMessage(role="assistant", content="Second feedback: needs improvement in B", metadata={}),
        AgentMessage(role="assistant", content="Perfect! FULLY_DONE = TRUE", metadata={}),
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
        execute_prompt="Do the work",
        execute_extra="Initial context",
        verify_prompt="Verify the work",
        verify_extra=None,
    )

    # then
    # Verify Execute phase called 3 times
    assert len(execute_agent.sent_messages) == 3

    # Verify Verify phase called 3 times
    assert len(verify_agent.sent_messages) == 3

    # 2nd Execute: Verify feedback 1 included
    second_execute_prompt = execute_agent.sent_messages[1]
    assert "<architect-feedback-history>" in second_execute_prompt
    assert '<feedback iteration="1">' in second_execute_prompt
    assert "First feedback: needs improvement in A" in second_execute_prompt

    # 3rd Execute: Verify feedback 1+2 included
    third_execute_prompt = execute_agent.sent_messages[2]
    assert '<feedback iteration="1">' in third_execute_prompt
    assert "First feedback: needs improvement in A" in third_execute_prompt
    assert '<feedback iteration="2">' in third_execute_prompt
    assert "Second feedback: needs improvement in B" in third_execute_prompt

    # 2nd Verify: Verify feedback history 1 included
    second_verify_prompt = verify_agent.sent_messages[1]
    assert "<previous_architect_reviews>" in second_verify_prompt
    assert '<review iteration="1">' in second_verify_prompt
    assert "First feedback: needs improvement in A" in second_verify_prompt

    # 3rd Verify: Verify feedback history 1+2 included
    third_verify_prompt = verify_agent.sent_messages[2]
    assert '<review iteration="1">' in third_verify_prompt
    assert "First feedback: needs improvement in A" in third_verify_prompt
    assert '<review iteration="2">' in third_verify_prompt
    assert "Second feedback: needs improvement in B" in third_verify_prompt


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
