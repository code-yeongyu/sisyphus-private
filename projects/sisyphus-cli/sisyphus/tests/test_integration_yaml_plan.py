"""Integration tests for v3.0 YAML work plan management."""

from __future__ import annotations

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from sisyphus.core.plans.loader import load_plan, save_plan
from sisyphus.core.plans.models import Metadata, PlanDocument, Todo, TodoStatus, WorkPlan
from sisyphus.core.task_manager import TaskManager

pytestmark = [pytest.mark.anyio]


async def test_end_to_end_workflow__full_cycle__completes_successfully(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "workflow.yaml"
    initial_plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-01-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="test-workflow",
                name="Test Workflow",
                depends_on=[],
                todos=[
                    Todo(id="1", title="First task", status=TodoStatus.pending, references=[]),
                    Todo(id="2", title="Second task", status=TodoStatus.pending, references=[]),
                ],
                references=[],
            )
        ],
    )

    # when - Step 1: Save and load YAML file
    yaml = YAML()
    with yaml_file.open("w") as f:
        yaml.dump(initial_plan.model_dump(mode="json", exclude_none=True), f)

    plan_doc = await load_plan(yaml_file)

    # then
    assert plan_doc.work_plans[0].todos[0].id == "1"
    assert plan_doc.work_plans[0].todos[0].status == TodoStatus.pending

    # when - Step 2: Get first pending task
    manager = TaskManager(plan_doc, "test-workflow")
    first_task = manager.get_next_task()

    # then
    assert first_task is not None
    assert first_task.id == "1"

    # when - Step 3: Update current_task_id and task status
    plan_doc.work_plans[0].work_mode.current_task_id = "1"
    plan_doc.work_plans[0].todos[0].status = TodoStatus.in_progress
    await save_plan(yaml_file, plan_doc)

    # when - Step 4: Reload and get next task
    reloaded_plan = await load_plan(yaml_file)
    reloaded_manager = TaskManager(reloaded_plan, "test-workflow")
    next_task = reloaded_manager.get_next_task()

    # then - Should return task 2 (task 1 in_progress, no children)
    assert next_task is not None
    assert next_task.id == "2"

    # when - Step 5: Mark first task completed
    reloaded_plan.work_plans[0].todos[0].status = TodoStatus.completed
    reloaded_plan.work_plans[0].work_mode.current_task_id = "2"
    reloaded_plan.work_plans[0].todos[1].status = TodoStatus.in_progress
    await save_plan(yaml_file, reloaded_plan)

    # when - Step 6: Reload and verify state
    final_plan = await load_plan(yaml_file)

    # then
    assert final_plan.work_plans[0].todos[0].status == TodoStatus.completed
    assert final_plan.work_plans[0].todos[1].status == TodoStatus.in_progress
    assert final_plan.work_plans[0].work_mode.current_task_id == "2"


async def test_nested_todos_navigation__complex_tree__navigates_correctly(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "nested.yaml"
    nested_plan = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-01-01T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id="nested-test",
                name="Nested Test",
                depends_on=[],
                todos=[
                    Todo(
                        id="1",
                        title="Parent task",
                        status=TodoStatus.in_progress,
                        references=[],
                        children=[
                            Todo(id="1.1", title="Child 1", status=TodoStatus.pending, references=[]),
                            Todo(id="1.2", title="Child 2", status=TodoStatus.pending, references=[]),
                        ],
                    ),
                    Todo(id="2", title="Second parent", status=TodoStatus.pending, references=[]),
                ],
                references=[],
            )
        ],
    )

    # Save initial plan
    yaml = YAML()
    with yaml_file.open("w") as f:
        yaml.dump(nested_plan.model_dump(mode="json", exclude_none=True), f)

    # when
    plan_doc = await load_plan(yaml_file)
    manager = TaskManager(plan_doc, "nested-test")

    # then - DFS navigation: children first
    next_task = manager.get_next_task(current_id="1")
    assert next_task is not None
    assert next_task.id == "1.1"

    # when - Complete 1.1, navigate to 1.2
    parent_todo = plan_doc.work_plans[0].todos[0]
    assert parent_todo.children is not None
    parent_todo.children[0].status = TodoStatus.completed
    next_after_11 = manager.get_next_task(current_id="1.1")

    # then
    assert next_after_11 is not None
    assert next_after_11.id == "1.2"

    # when - Complete 1.2, should backtrack to parent's sibling
    parent_todo.children[1].status = TodoStatus.completed
    plan_doc.work_plans[0].todos[0].status = TodoStatus.completed
    manager_updated = TaskManager(plan_doc, "nested-test")
    next_after_12 = manager_updated.get_next_task(current_id="1.2")

    # then
    assert next_after_12 is not None
    assert next_after_12.id == "2"
