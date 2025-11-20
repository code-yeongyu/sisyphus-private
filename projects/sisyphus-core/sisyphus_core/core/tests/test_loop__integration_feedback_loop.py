# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false
"""Integration tests for ExecutionLoop complete feedback loop."""

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
        execute_prompt="Do the work",
        execute_extra=None,
        verify_prompt="Verify the work",
        verify_extra=None,
    )

    # then
    assert len(execute_agent.sent_messages) == 1
    assert len(verify_agent.sent_messages) == 1
    assert task_validator.call_count == 3


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
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [False, False, False, True]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(plan_path=str(task_validator.todolist_path)),  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

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


async def test_feedback_loop__scenario_3_verify_feedback_iteration() -> None:
    """Scenario 3: Multiple Verify feedback iterations → Accumulate → Final success."""
    # given
    execute_agent = MockAgent()
    execute_agent.response_sequence = [
        [AgentMessage(role="assistant", content="Work iteration 1", metadata={})],
        [AgentMessage(role="assistant", content="Work iteration 2", metadata={})],
        [AgentMessage(role="assistant", content="Work iteration 3", metadata={})],
        [AgentMessage(role="assistant", content="Work iteration 4", metadata={})],
        [AgentMessage(role="assistant", content="Work iteration 5", metadata={})],
    ]
    verify_agent = MockAgent()
    verify_agent.response_sequence = [
        [
            AgentMessage(
                role="assistant", content="First feedback: needs improvement in A\nFULLY_DONE = FALSE", metadata={}
            )
        ],
        [
            AgentMessage(
                role="assistant", content="Second feedback: needs improvement in B\nFULLY_DONE = FALSE", metadata={}
            )
        ],
        [AgentMessage(role="assistant", content="Perfect! FULLY_DONE = TRUE", metadata={})],
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [False, False, True, False, True, False, True, True, True, True]

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
        execute_prompt="Do the work",
        execute_extra="Initial context",
        verify_prompt="Verify the work",
        verify_extra=None,
    )

    # then
    # Verify Execute phase called at least 3 times
    assert len(execute_agent.sent_messages) >= 3

    # Verify Verify phase called 3 times
    assert len(verify_agent.sent_messages) == 3

    # 2nd Execute: Verify feedback 1 included
    second_execute_prompt = execute_agent.sent_messages[1]
    assert "<verify-feedback-history>" in second_execute_prompt
    assert '<feedback iteration="1">' in second_execute_prompt
    assert "First feedback: needs improvement in A" in second_execute_prompt

    # Last Execute: Verify feedback 1+2 included
    last_execute_prompt = execute_agent.sent_messages[-1]
    assert '<feedback iteration="1">' in last_execute_prompt
    assert "First feedback: needs improvement in A" in last_execute_prompt
    assert '<feedback iteration="2">' in last_execute_prompt
    assert "Second feedback: needs improvement in B" in last_execute_prompt

    # 2nd Verify: Verify feedback history 1 included
    second_verify_prompt = verify_agent.sent_messages[1]
    assert "<previous_verify_reviews>" in second_verify_prompt
    assert '<review iteration="1">' in second_verify_prompt
    assert "First feedback: needs improvement in A" in second_verify_prompt

    # 3rd Verify: Verify feedback history 1+2 included
    third_verify_prompt = verify_agent.sent_messages[2]
    assert '<review iteration="1">' in third_verify_prompt
    assert "First feedback: needs improvement in A" in third_verify_prompt
    assert '<review iteration="2">' in third_verify_prompt
    assert "Second feedback: needs improvement in B" in third_verify_prompt


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
    def create_logger(_agent_type: str, _session_id: str | None = None, _log_dir: Path | None = None) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        logger.warning = MagicMock()
        return logger
