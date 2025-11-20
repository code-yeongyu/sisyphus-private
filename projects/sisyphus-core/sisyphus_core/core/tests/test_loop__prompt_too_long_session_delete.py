# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false
"""Tests for ExecutionLoop PromptTooLongError session deletion."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.session import SessionStore
from sisyphus_core.core.tests.test_loop import MockAgent, MockStatusManager
from sisyphus_core.utils.errors import PromptTooLongError
from sisyphus_core.utils.types import AgentMessage

pytestmark = [pytest.mark.anyio]


@pytest.fixture()
async def test_plan_file(tmp_path: Path) -> Path:
    plan_dir = tmp_path / ".sisyphus" / "tasks"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "test-plan.yaml"
    _ = plan_file.write_text("""version: "3.0"
metadata:
  created_at: "2025-11-12T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
    depends_on: []
    user_request:
      original: Test
      created_at: "2025-11-12T00:00:00Z"
      additional: []
    objectives:
      core: Test
      detailed: []
    background:
      current_situation: Test
      reason_for_change: Test
      changes_to_make: Test
    required_background:
      description: Test
      references: []
    workflow:
      dependency_diagram: ""
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos: []
    references: []
""")
    return plan_file


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

    async def send(self, _message: str) -> None:
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


class MockTaskValidator:
    def __init__(self, all_complete: bool = False, todolist_path: Path | None = None, complete_after: int = 6) -> None:
        self._all_complete = all_complete
        self.call_count = 0
        self.todolist_path = todolist_path or Path(".sisyphus/tasks/test-plan.yaml")
        self.complete_after = complete_after

    def read_content(self) -> str:
        return "mock content"

    async def check_all_goals_accomplished(self, _content: str | None = None) -> bool:
        if self.call_count >= self.complete_after:
            return True
        return self._all_complete

    async def check_all_checkboxes_completed(self, content: str | None = None) -> bool:
        result = await self.check_all_goals_accomplished(content)
        self.call_count += 1
        return result

    def extract_uncompleted_checkboxes(self, _content: str | None = None) -> list[str]:
        return []

    def count_total_checkboxes(self, _content: str | None = None) -> int:
        return 1

    def count_completed_checkboxes(self, _content: str | None = None) -> int:
        return 1 if self._all_complete else 0


async def test_execution_loop__if_prompt_too_long_error__deletes_session(tmp_path: Path, test_plan_file: Path) -> None:
    """Test that PromptTooLongError triggers session deletion."""
    # given
    session_dir = tmp_path / "sessions"
    session_store = SessionStore(base_dir=session_dir)

    await session_store.save_session("mockwithprompterror", "old-session-id", "test-plan")

    agent = MockAgentWithPromptError(fail_count=1)
    ui = MockUI()
    logger_factory = MagicMock()
    logger_factory.create_logger.return_value = MagicMock()

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]

    loop = ExecutionLoop(
        execute_agent=agent,
        verify_agent=verify_agent,
        ui=ui,
        session_store=session_store,
        logger_factory=logger_factory,
        task_validator=MockTaskValidator(all_complete=False, todolist_path=test_plan_file, complete_after=6),
        status_manager=MockStatusManager(),
    )

    loop.state.set_plan_id("test-plan")

    # when
    await loop.run()

    # then
    sessions = await session_store.list_sessions()
    assert sessions["mockwithprompterror"]["test-plan"]["session_id"] != "old-session-id"
    assert sessions["mockwithprompterror"]["test-plan"]["session_id"] == "new-session-123"

    assert any("Session 'mockwithprompterror' cleared" in msg for msg in ui.status_messages)
    assert any("prompt length exceeded" in msg for msg in ui.status_messages)


async def test_execution_loop__if_prompt_too_long_error__starts_new_session(
    tmp_path: Path, test_plan_file: Path
) -> None:
    """Test that after session deletion, new session is started."""
    # given
    session_dir = tmp_path / "sessions"
    session_store = SessionStore(base_dir=session_dir)

    await session_store.save_session("mockwithprompterror", "old-session-id", "test-plan")

    agent = MockAgentWithPromptError(fail_count=1)
    ui = MockUI()
    logger_factory = MagicMock()
    logger_factory.create_logger.return_value = MagicMock()

    verify_agent = MockAgent()
    verify_agent.messages_to_return = [AgentMessage(role="assistant", content="FULLY_DONE = TRUE")]

    loop = ExecutionLoop(
        execute_agent=agent,
        verify_agent=verify_agent,
        ui=ui,
        session_store=session_store,
        logger_factory=logger_factory,
        task_validator=MockTaskValidator(all_complete=False, todolist_path=test_plan_file, complete_after=4),
        status_manager=MockStatusManager(),
    )

    loop.state.set_plan_id("test-plan")

    # when
    await loop.run()

    # then
    assert agent.call_count == 2
    assert len(ui.messages) == 2
    assert ui.messages[0].content == "Success after session reset"
    assert "FULLY_DONE = TRUE" in ui.messages[1].content
