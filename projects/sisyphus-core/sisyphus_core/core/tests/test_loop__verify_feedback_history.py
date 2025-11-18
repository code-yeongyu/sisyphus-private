# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false
"""Tests for ExecutionLoop verify feedback history injection."""

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


async def test_verify__if_no_feedback_history__uses_original_prompt() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.all_complete = True

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

    original_verify_prompt = "Please verify the work."

    # when
    await loop._run_unified_mode(
        execute_prompt="Do work",
        execute_extra=None,
        verify_prompt=original_verify_prompt,
        verify_extra=None,
    )

    # then
    assert len(verify_agent.sent_messages) == 1
    sent_prompt = verify_agent.sent_messages[0]

    assert sent_prompt == original_verify_prompt
    assert "<previous_verify_reviews>" not in sent_prompt


async def test_verify__if_feedback_history_exists__prepends_history_section() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Work done", metadata={}),
    ]
    verify_agent = MockAgent()

    verify_agent.response_sequence = [
        [AgentMessage(role="assistant", content="First feedback: needs improvement\nFULLY_DONE = FALSE", metadata={})],
        [AgentMessage(role="assistant", content="FULLY_DONE = TRUE", metadata={})],
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator()
    task_validator.completion_sequence = [True, True]

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

    original_verify_prompt = "Please verify the work."

    # when
    await loop._run_unified_mode(
        execute_prompt="Do work",
        execute_extra=None,
        verify_prompt=original_verify_prompt,
        verify_extra=None,
    )

    # then
    assert len(verify_agent.sent_messages) == 2

    second_verify_prompt = verify_agent.sent_messages[1]

    assert "<previous_verify_reviews>" in second_verify_prompt
    assert '<review iteration="1">' in second_verify_prompt
    assert "First feedback: needs improvement" in second_verify_prompt
    assert "</previous_verify_reviews>" in second_verify_prompt
    assert second_verify_prompt.endswith(original_verify_prompt)


async def test_verify__if_multiple_feedbacks__includes_all_in_history() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Work done", metadata={}),
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
    task_validator.completion_sequence = [True, True, True]

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

    original_verify_prompt = "Please verify the work."

    # when
    await loop._run_unified_mode(
        execute_prompt="Do work",
        execute_extra=None,
        verify_prompt=original_verify_prompt,
        verify_extra=None,
    )

    # then
    assert len(verify_agent.sent_messages) == 3

    third_verify_prompt = verify_agent.sent_messages[2]

    assert '<review iteration="1">' in third_verify_prompt
    assert "First feedback" in third_verify_prompt
    assert '<review iteration="2">' in third_verify_prompt
    assert "Second feedback" in third_verify_prompt
    assert "</previous_verify_reviews>" in third_verify_prompt

    history_start = third_verify_prompt.index("<previous_verify_reviews>")
    history_end = third_verify_prompt.index("</previous_verify_reviews>")
    first_feedback_pos = third_verify_prompt.index("First feedback")
    second_feedback_pos = third_verify_prompt.index("Second feedback")

    assert history_start < first_feedback_pos < second_feedback_pos < history_end


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
