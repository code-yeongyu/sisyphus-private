from __future__ import annotations

import pytest

from sisyphus_core.core.plans.models import (
    Background,
    Metadata,
    Objectives,
    PlanDocument,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkPlan,
)
from sisyphus_core.core.task_manager import TaskManager

pytestmark = [pytest.mark.anyio]


def create_minimal_plan(plan_id: str, todos: list[Todo]) -> PlanDocument:
    return PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-06T00:00:00Z"),
        work_plans=[
            WorkPlan(
                id=plan_id,
                name="Test Plan",
                user_request=UserRequest(original="Test", created_at="2025-11-06T00:00:00Z", additional=[]),
                objectives=Objectives(core="Test", detailed=[]),
                background=Background(current_situation="Test", reason_for_change="Test", changes_to_make="Test"),
                required_background=RequiredBackground(description="Test", file_structure=None, references=[]),
                workflow=Workflow(dependency_diagram="Test", critical_path=[]),
                success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
                final_verification=[],
                todos=todos,
            )
        ],
    )


async def test_task_manager__if_valid_plan__finds_work_plan() -> None:
    # given
    plan_doc = create_minimal_plan("test-plan", [])

    # when
    manager = TaskManager(plan_doc, "test-plan")

    # then
    assert manager.work_plan.id == "test-plan"


async def test_task_manager__if_missing_plan__raises_error() -> None:
    # given
    plan_doc = PlanDocument(version="3.0", metadata=Metadata(created_at="2025-11-06T00:00:00Z"), work_plans=[])

    # when & then
    with pytest.raises(ValueError, match="WorkPlan not found"):
        TaskManager(plan_doc, "missing-plan")


async def test_find_todo_by_id__if_root_todo__returns_it() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending)]
    plan_doc = create_minimal_plan("test-plan", todos)
    manager = TaskManager(plan_doc, "test-plan")

    # when
    todo = manager.find_todo_by_id("1")

    # then
    assert todo is not None
    assert todo.id == "1"


async def test_get_next_task__if_no_current__returns_first_pending() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.completed),
        Todo(id="2", title="Task 2", status=TodoStatus.pending),
    ]
    plan_doc = create_minimal_plan("test-plan", todos)
    manager = TaskManager(plan_doc, "test-plan")

    # when
    next_task = manager.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "2"
