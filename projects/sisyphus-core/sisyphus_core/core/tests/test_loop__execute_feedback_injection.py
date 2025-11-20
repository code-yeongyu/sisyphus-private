"""Tests for ExecutionLoop feedback injection to execute phase."""
# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.tests.test_loop import MockAgent, MockStatusManager, MockTaskValidator
from sisyphus_core.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


async def test_execute__if_no_feedback_history__uses_original_extra() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Work completed", metadata={}),
    ]
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [False, False, True]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    # when
    await loop._run_unified_mode(
        execute_prompt="Do the task",
        execute_extra="Original extra content",
        verify_prompt="Verify the task",
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 1
    sent_prompt = execute_agent.sent_messages[0]
    assert "Original extra content" in sent_prompt
    assert "Verify Feedback" not in sent_prompt


async def test_execute__if_feedback_history_exists__appends_feedback_section() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.response_sequence = [
        [AgentMessage(role="assistant", content="Work done", metadata={})],
        [AgentMessage(role="assistant", content="Work done again", metadata={})],
    ]
    verify_agent = MockAgent()

    verify_agent.response_sequence = [
        [AgentMessage(role="assistant", content="Please fix the bug\nFULLY_DONE = FALSE", metadata={})],
        [AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={})],
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [False, False, True, False, True]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    # when
    await loop._run_unified_mode(
        execute_prompt="Do the task",
        execute_extra="Original extra",
        verify_prompt="Verify the task",
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 2

    first_execution = execute_agent.sent_messages[0]
    assert "Verify Feedback" not in first_execution

    second_execution = execute_agent.sent_messages[1]
    assert "Original extra" in second_execution
    assert "🔍 Verify Feedback from Previous Iterations" in second_execution
    assert "<verify-feedback-history>" in second_execution
    assert '<feedback iteration="1">' in second_execution
    assert "Please fix the bug" in second_execution
    assert "**CRITICAL**: Address ALL issues" in second_execution


async def test_execute__if_multiple_feedbacks__includes_all_with_correct_numbering() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.response_sequence = [
        [AgentMessage(role="assistant", content="Work iteration 1", metadata={})],
        [AgentMessage(role="assistant", content="Work iteration 2", metadata={})],
        [AgentMessage(role="assistant", content="Work iteration 3", metadata={})],
    ]
    verify_agent = MockAgent()

    verify_agent.response_sequence = [
        [AgentMessage(role="assistant", content="First feedback\nFULLY_DONE = FALSE", metadata={})],
        [AgentMessage(role="assistant", content="Second feedback\nFULLY_DONE = FALSE", metadata={})],
        [AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={})],
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [False, False, True, False, True, False, True]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    # when
    await loop._run_unified_mode(
        execute_prompt="Do the task",
        execute_extra=None,
        verify_prompt="Verify the task",
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) >= 3

    last_execution = execute_agent.sent_messages[-1]
    assert '<feedback iteration="1">' in last_execution
    assert "First feedback" in last_execution
    assert '<feedback iteration="2">' in last_execution
    assert "Second feedback" in last_execution

    first_idx = last_execution.index('<feedback iteration="1">')
    second_idx = last_execution.index('<feedback iteration="2">')
    assert first_idx < second_idx


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

    async def get_session(self, agent_type: str, _plan_id: str) -> str | None:
        return self.sessions.get(agent_type)

    async def save_session(self, agent_type: str, session_id: str, _plan_id: str) -> None:
        self.sessions[agent_type] = session_id

    async def delete_session(self, agent_type: str, _plan_id: str | None = None) -> None:
        if agent_type in self.sessions:
            del self.sessions[agent_type]

    async def list_sessions(self) -> dict[str, dict[str, str]]:
        return {k: {"session_id": v} for k, v in self.sessions.items()}


class MockLoggerFactory:
    """Mock logger factory for testing."""

    @staticmethod
    def create_logger(agent_type: str, session_id: str | None = None, _log_dir: Path = Path("./logs")) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.warning = MagicMock()
        return logger
