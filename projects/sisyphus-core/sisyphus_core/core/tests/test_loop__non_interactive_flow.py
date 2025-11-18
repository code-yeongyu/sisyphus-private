# pyright: reportArgumentType=false, reportMissingImports=false, reportImplicitRelativeImport=false
"""Tests for ExecutionLoop._run_unified_mode flow control."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sisyphus_core.core.loop import ExecutionLoop
from sisyphus_core.core.tests.test_loop import (
    MockAgent,
    MockLoggerFactory,
    MockSessionStore,
    MockStatusManager,
    MockUI,
)
from sisyphus_core.utils.types import AgentMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.anyio]


@pytest.fixture()
async def test_plan_file(tmp_path: Path) -> Path:
    plan_dir = tmp_path / ".sisyphus" / "tasks"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "test-plan.yaml"
    plan_file.write_text("""version: "3.0"
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


async def test_unified__if_task_incomplete__skips_verify_and_retries_execute(test_plan_file: Path) -> None:
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

    task_validator = MockTaskValidator(todolist_path=test_plan_file)
    task_validator.check_results = [
        (False, False),  # Initial check
        (False, False),  # Skip_execute check (iteration==1)
        (False, False),  # After first execute (incomplete, retry)
        (False, False),  # Skip_execute check (iteration==2)
        (True, True),  # After second execute (complete, verify)
    ]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 5
    assert len(execute_agent.sent_messages) == 2
    assert len(verify_agent.sent_messages) == 1


async def test_unified__if_task_complete_and_fully_done__exits_loop(test_plan_file: Path) -> None:
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

    task_validator = MockTaskValidator(todolist_path=test_plan_file)
    task_validator.check_results = [(True, True)]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 3
    assert len(verify_agent.sent_messages) == 1
    assert any("FULLY_DONE" in status for status in ui.statuses)


async def test_unified__if_task_complete_but_not_fully_done__continues_with_feedback(test_plan_file: Path) -> None:
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

    task_validator = MockTaskValidator(todolist_path=test_plan_file)
    task_validator.check_results = [
        (False, False),  # Initial check
        (False, False),  # Skip_execute check (iteration==1)
        (True, True),  # After first execute -> verify
        (False, False),  # Skip_execute check (iteration==2, incomplete after verify feedback)
        (True, True),  # After second execute -> verify (with feedback)
    ]

    loop = ExecutionLoop(
        execute_agent=execute_agent,  # type: ignore[arg-type]
        ui=ui,  # type: ignore[arg-type]
        session_store=session_store,  # type: ignore[arg-type]
        logger_factory=logger_factory,  # type: ignore[arg-type]
        verify_agent=verify_agent,  # type: ignore[arg-type]
        task_validator=task_validator,  # type: ignore[arg-type]
        status_manager=MockStatusManager(),  # type: ignore[arg-type]
    )

    # when
    await loop._run_unified_mode("execute prompt", None, "verify prompt", None)

    # then
    assert task_validator.check_call_count == 5
    assert len(execute_agent.sent_messages) == 2
    assert len(verify_agent.sent_messages) == 2


class MockTaskValidator:
    """Mock task validator for testing."""

    def __init__(self, todolist_path: Path | None = None) -> None:
        self.check_results: list[tuple[bool, bool]] = []
        self.check_call_count = 0
        self.todolist_path = todolist_path or Path(".sisyphus/tasks/test-plan.yaml")

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
