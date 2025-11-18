"""Tests for ExecutionLoop."""
# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false

from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.status.manager import CurrentPlan, StatusFile
from sisyphus_core.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


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
        self._messages_consumed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def start_session(self, session_id: str | None = None) -> str:
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = f"session-{self.session_count}"
            self.session_count += 1
        self._messages_consumed = False
        return self.session_id

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    def stream(self) -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            if self.response_sequence:
                if self.message_index < len(self.response_sequence):
                    for msg in self.response_sequence[self.message_index]:
                        yield msg
                    self.message_index += 1
            elif not self._messages_consumed:
                for msg in self.messages_to_return:
                    yield msg
                self._messages_consumed = True

        return _generator()

    async def close(self) -> None:
        self.closed = True


class MockUI:
    """Mock UI for testing."""

    def __init__(self) -> None:
        self.initialized = False
        self.messages: list[tuple[AgentMessage, str]] = []
        self.statuses: list[str] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def show_message(self, message: AgentMessage, source: str) -> None:
        self.messages.append((message, source))

    async def show_status(self, status: str) -> None:
        self.statuses.append(status)

    async def get_input(self) -> str | None:
        return None


class MockSessionStore:
    """Mock session store for testing."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, str]] = {}

    async def get_session(self, agent_type: str, plan_id: str) -> str | None:
        if agent_type not in self.sessions:
            return None
        return self.sessions[agent_type].get(plan_id)

    async def save_session(self, agent_type: str, session_id: str, plan_id: str) -> None:
        if agent_type not in self.sessions:
            self.sessions[agent_type] = {}
        self.sessions[agent_type][plan_id] = session_id

    async def delete_session(self, agent_type: str, plan_id: str | None = None) -> None:
        if plan_id is None:
            if agent_type in self.sessions:
                del self.sessions[agent_type]
        else:
            if agent_type in self.sessions and plan_id in self.sessions[agent_type]:
                del self.sessions[agent_type][plan_id]
                if not self.sessions[agent_type]:
                    del self.sessions[agent_type]

    async def list_sessions(self) -> dict[str, dict[str, str]]:
        return self.sessions


class MockLoggerFactory:
    """Mock logger factory for testing."""

    @staticmethod
    def create_logger(agent_type: str, session_id: str | None = None, log_dir: Path = Path("./logs")) -> MagicMock:
        logger = MagicMock()
        logger.info = MagicMock()
        logger.debug = MagicMock()
        return logger


class MockTaskValidator:
    """Mock task validator for testing."""

    def __init__(self, all_complete: bool = False) -> None:
        self._all_complete = all_complete
        self.completion_sequence: list[bool] = []
        self.call_count = 0
        self.read_count = 0
        self._isolated_temp_dir = tempfile.mkdtemp()
        self.todolist_path = Path(self._isolated_temp_dir) / "test-plan.yaml"
        self._create_test_plan_file()

    def _create_test_plan_file(self) -> None:
        content = """version: '3.0'
metadata:
  created_at: '2025-11-12T00:00:00Z'
work_plans:
- id: test-plan
  name: Test Plan
  user_request:
    original: Test request
    created_at: '2025-11-12T00:00:00Z'
  objectives:
    core: Test objective
    detailed: []
  background:
    current_situation: Test situation
    reason_for_change: Test reason
    changes_to_make: Test changes
  required_background:
    description: Test background
    references: []
  workflow:
    dependency_diagram: Test diagram
    critical_path: []
  success_vision:
    user_perspective: []
    business_perspective: []
    technical_criteria: []
  final_verification: []
  todos: []
  work_mode:
    mode: sequential
    current_task_id: null
    parallel_requested: false
  execution:
    started: false
    completed: false
"""
        self.todolist_path.parent.mkdir(parents=True, exist_ok=True)
        self.todolist_path.write_text(content)

    def read_content(self) -> str:
        self.read_count += 1
        return "mock content"

    async def check_all_goals_accomplished(self, content: str | None = None) -> bool:
        if self.completion_sequence:
            idx = min(self.call_count, len(self.completion_sequence) - 1)
            result = self.completion_sequence[idx]
            self.call_count += 1
            return result
        return self._all_complete

    async def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        if self.completion_sequence:
            current_check_index = max(0, self.call_count - 1)
            sequence_index = min(current_check_index, len(self.completion_sequence) - 1)
            return self.completion_sequence[sequence_index]
        return self._all_complete

    def extract_uncompleted_checkboxes(self, content: str | None = None) -> list[str]:
        if self._all_complete:
            return []
        return ["Task 1", "Task 2"]

    def count_total_checkboxes(self, content: str | None = None) -> int:
        return 10

    def count_completed_checkboxes(self, content: str | None = None) -> int:
        return 8 if not self._all_complete else 10


class MockStatusManager:
    """Mock StatusManager for testing."""

    def __init__(self, plan_id: str = "test-plan") -> None:
        self.plan_id = plan_id

    async def get(self) -> StatusFile:
        return StatusFile(
            current_plan=CurrentPlan(
                plan_path=".sisyphus/tasks/test-plan.yaml",
                plan_root=".sisyphus/tasks",
                updated_at="2025-11-10T00:00:00Z",
            )
        )

    async def set_current(self, plan_path: str, plan_root: str) -> None:
        """No-op for tests."""
        pass

    async def get_plan_id(self) -> str:
        """Return plan_id directly without loading YAML."""
        return self.plan_id


async def test_execution_loop_execute_only() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Hello from execute", metadata={}),
    ]
    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=False)
    task_validator.completion_sequence = [False, False, True]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run()

    # then
    assert execute_agent.initialized
    assert execute_agent.session_id == "session-0"
    assert len(execute_agent.sent_messages) > 0
    assert "sisyphus" in execute_agent.sent_messages[0].lower()
    assert execute_agent.closed
    assert ui.initialized
    # UI remains initialized after ExecutionLoop completes (no longer closes automatically)
    assert len(ui.messages) == 2
    assert ui.messages[0][0].content == "Hello from execute"
    assert ui.messages[0][1] == "execute"
    assert ui.messages[1][0].content == "FULLY_DONE = TRUE"
    assert ui.messages[1][1] == "verify"


async def test_execution_loop_execute_and_verify() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Execute done", metadata={}),
    ]

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Verify done\n\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator(all_complete=False)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    loop.state.set_plan_id("test-plan")

    original_execute = loop.phase_orchestrator.execute_phase

    async def patched_execute_phase(prompt: str, extra: str | None = None) -> None:
        task_validator._all_complete = True
        await original_execute(prompt, extra)

    loop.phase_orchestrator.execute_phase = patched_execute_phase  # type: ignore[method-assign]

    # when
    await loop.run()

    # then
    assert execute_agent.initialized
    assert verify_agent.initialized
    assert execute_agent.closed
    assert verify_agent.closed
    assert len(ui.messages) == 2
    assert ui.messages[0][1] == "execute"
    assert ui.messages[1][1] == "verify"


async def test_execution_loop_verify_always_new_session() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Verify complete\n\nFULLY_DONE = TRUE", metadata={}),
    ]

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mockagent", "old-session-456", "default")
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run()

    # then
    assert verify_agent.session_id == "session-0"


async def test_execution_loop_session_resume() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=False)

    ui = MockUI()
    session_store = MockSessionStore()
    await session_store.save_session("mock", "existing-session-789", "test-plan")
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run()

    # then
    assert execute_agent.session_id == "existing-session-789"


async def test_execution_loop_with_task_validator_complete() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()
    task_validator = MockTaskValidator(all_complete=True)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run()

    # then
    assert task_validator.read_count >= 1
    assert any("All tasks completed" in s or "already completed" in s for s in ui.statuses)


async def test_execution_loop_with_task_validator_incomplete() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    validator = MockTaskValidator(all_complete=False)

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    iteration_count = 0

    original_run = loop.phase_orchestrator.execute_phase

    async def patched_execute_phase(prompt: str, extra: str | None = None) -> None:
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 2:
            validator._all_complete = True
        await original_run(prompt, extra)

    loop.phase_orchestrator.execute_phase = patched_execute_phase  # type: ignore[method-assign]

    # when
    await loop.run()

    # then
    assert iteration_count == 2
    assert validator.read_count >= 2


async def test_execution_loop_prompt_with_extra() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=False)

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run(execute_extra="Extra info")

    # then
    assert len(execute_agent.sent_messages) > 0
    assert "Extra info" in execute_agent.sent_messages[0]
    assert "sisyphus" in execute_agent.sent_messages[0].lower()


async def test_execution_loop_ui_status_updates() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=True)

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run()

    # then
    assert any("Execute phase" in s for s in ui.statuses)
    assert any("complete" in s for s in ui.statuses)


async def test_execution_loop_session_saved() -> None:
    # given
    execute_agent = MockAgent()
    execute_agent.messages_to_return = []

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]
    task_validator = MockTaskValidator(all_complete=False)

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore
        verify_agent=verify_agent,  # type: ignore
        ui=ui,  # type: ignore
        session_store=session_store,  # type: ignore
        logger_factory=logger_factory,  # type: ignore
        task_validator=task_validator,  # type: ignore
        status_manager=MockStatusManager(),  # type: ignore
    )

    # when
    await loop.run()

    # then
    sessions = await session_store.list_sessions()
    assert "mock" in sessions
    assert "test-plan" in sessions["mock"]
    assert sessions["mock"]["test-plan"] == "session-0"


async def test_verify_phase__if_middle_message_has_true_but_last_has_false__returns_false() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Checking... FULLY_DONE = TRUE in thinking", metadata={}),
        AgentMessage(role="assistant", content="Actually, FULLY_DONE = FALSE", metadata={}),
    ]
    task_validator = MockTaskValidator(all_complete=True)

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    # when
    feedback, fully_done = await loop.phase_orchestrator.verify_phase(
        prompt="Test prompt",
        extra=None,
    )

    # then
    assert fully_done is False
    assert len(verify_agent.sent_messages) == 1


async def test_verify_phase__if_no_judgment__retries_until_found() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()

    call_count = 0

    def stream_generator() -> AsyncIterator[AgentMessage]:
        async def _generator() -> AsyncIterator[AgentMessage]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                yield AgentMessage(role="assistant", content="Still analyzing...", metadata={})
            else:
                yield AgentMessage(role="assistant", content="FULLY_DONE = FALSE", metadata={})

        return _generator()

    verify_agent.stream = stream_generator  # type: ignore[method-assign]
    task_validator = MockTaskValidator(all_complete=True)

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    # when
    feedback, fully_done = await loop.phase_orchestrator.verify_phase(
        prompt="Test prompt",
        extra=None,
    )

    # then
    assert fully_done is False
    assert len(verify_agent.sent_messages) == 2


async def test_verify_phase__if_max_retries_exceeded__defaults_to_false() -> None:
    # given
    execute_agent = MockAgent()
    verify_agent = MockAgent()
    verify_agent.messages_to_return = [
        AgentMessage(role="assistant", content="Still analyzing...", metadata={}),
    ]
    task_validator = MockTaskValidator(all_complete=True)

    ui = MockUI()
    session_store = MockSessionStore()
    logger_factory = MockLoggerFactory()

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
    )

    loop.state.set_plan_id("test-plan")

    # when
    feedback, fully_done = await loop.phase_orchestrator.verify_phase(
        prompt="Test prompt",
        extra=None,
    )

    # then
    assert fully_done is False
    assert len(verify_agent.sent_messages) == 6
