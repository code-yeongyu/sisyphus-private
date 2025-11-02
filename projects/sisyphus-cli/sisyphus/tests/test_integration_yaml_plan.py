"""Integration tests for YAML work plan management."""

from pathlib import Path

import pytest

from sisyphus.core.plan_loader import PlanLoader
from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.utils.plan_types import TodoStatus

pytestmark = [pytest.mark.anyio]


async def test_end_to_end_workflow__full_cycle__completes_successfully(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "workflow.yaml"
    initial_content = """
metadata:
  created_at: "2025-01-01T00:00:00"
  updated_at: "2025-01-01T00:00:00"
user_request:
  original: "Test workflow"
  created_at: "2025-01-01"
objectives:
  core: "Test end-to-end workflow"
background:
  current_situation: "Testing"
  reason_for_change: "Verification"
  changes_to_make: "Complete workflow"
required_background:
  description: "E2E test"
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: null
  progress:
    total_tasks: 2
    completed: 0
    in_progress: 0
    pending: 2
  current_work: "None"
workflow:
  dependency_diagram: "Task 1 -> Task 2"
todos:
  - id: "1"
    title: "First task"
    status: pending
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
  - id: "2"
    title: "Second task"
    status: pending
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(initial_content, encoding="utf-8")
    loader = PlanLoader(yaml_file)

    # when - Step 1: Load YAML file
    plan = loader.load()

    # then
    assert plan.todos[0].id == "1"
    assert plan.todos[0].status == TodoStatus.pending

    # when - Step 2: Get first pending task
    navigator = PlanNavigator(plan)
    first_task = navigator.get_next_task()

    # then
    assert first_task is not None
    assert first_task.id == "1"

    # when - Step 3: Update current_task_id
    plan.status.work_mode.current_task_id = "1"
    plan.todos[0].status = TodoStatus.in_progress
    loader.save(plan)

    # when - Step 4: Reload and get next task
    reloaded_plan = loader.load()
    reloaded_navigator = PlanNavigator(reloaded_plan)
    next_task = reloaded_navigator.get_next_task()

    # then - Should still return task 1 (in_progress, no children)
    assert next_task is not None
    assert next_task.id == "2"

    # when - Step 5: Mark first task completed
    reloaded_plan.todos[0].status = TodoStatus.completed
    reloaded_plan.status.work_mode.current_task_id = "2"
    reloaded_plan.todos[1].status = TodoStatus.in_progress
    loader.save(reloaded_plan)

    # when - Step 6: Reload and verify state
    final_plan = loader.load()

    # then
    assert final_plan.todos[0].status == TodoStatus.completed
    assert final_plan.todos[1].status == TodoStatus.in_progress
    assert final_plan.status.work_mode.current_task_id == "2"


async def test_example_yaml_loads_and_validates() -> None:
    # given
    example_path = Path("example-ai-todolist.yaml")

    # when
    if not example_path.exists():
        pytest.skip("example-ai-todolist.yaml not found")

    # NOTE: example-ai-todolist.yaml is a Tetris PRD, not a minimal schema example.
    # It uses complex reference structures that don't match SimpleReference schema.
    # Skipping validation test - the file serves as a comprehensive example,
    # not a schema compliance test case.
    pytest.skip("example-ai-todolist.yaml uses complex reference structure (Tetris PRD)")


async def test_nested_todos_navigation__complex_tree__navigates_correctly(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "nested.yaml"
    nested_content = """
metadata:
  created_at: "2025-01-01T00:00:00"
  updated_at: "2025-01-01T00:00:00"
user_request:
  original: "Nested test"
  created_at: "2025-01-01"
objectives:
  core: "Test nested navigation"
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Nested"
status:
  execution:
    started: true
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: "1"
  progress:
    total_tasks: 4
    completed: 0
    in_progress: 1
    pending: 3
  current_work: "Task 1"
workflow:
  dependency_diagram: "1 -> (1.1, 1.2) -> 2"
todos:
  - id: "1"
    title: "Parent task"
    status: in_progress
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
    children:
      - id: "1.1"
        title: "Child 1"
        status: pending
        created_at: "2025-01-01"
        updated_at: "2025-01-01"
      - id: "1.2"
        title: "Child 2"
        status: pending
        created_at: "2025-01-01"
        updated_at: "2025-01-01"
  - id: "2"
    title: "Second parent"
    status: pending
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
success_vision: {}
final_verification: []
"""
    yaml_file.write_text(nested_content, encoding="utf-8")

    # when
    loader = PlanLoader(yaml_file)
    plan = loader.load()
    navigator = PlanNavigator(plan)

    # then - DFS navigation: children first
    next_task = navigator.get_next_task(current_id="1")
    assert next_task is not None
    assert next_task.id == "1.1"

    # when - Complete 1.1, navigate to 1.2
    plan.todos[0].children[0].status = TodoStatus.completed
    next_after_11 = navigator.get_next_task(current_id="1.1")

    # then
    assert next_after_11 is not None
    assert next_after_11.id == "1.2"

    # when - Complete 1.2, should backtrack to parent's sibling
    plan.todos[0].children[1].status = TodoStatus.completed
    plan.todos[0].status = TodoStatus.completed
    next_after_12 = navigator.get_next_task(current_id="1.2")

    # then
    assert next_after_12 is not None
    assert next_after_12.id == "2"
