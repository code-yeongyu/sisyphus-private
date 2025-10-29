"""End-to-end integration tests for task filtering and completion tracking."""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus.core.plan_loader import PlanLoader
from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.utils.plan_types import (
    Background,
    CommandInput,
    ExecutionStatus,
    Metadata,
    NoneVerify,
    Objectives,
    Progress,
    RequiredBackground,
    Status,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    VerificationItem,
    Workflow,
    WorkMode,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


async def test_end_to_end_workflow__load_query_update_verify_save_reload__data_persists(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "integration_test.yaml"

    child1 = Todo(
        id="1.1",
        title="Child Task 1",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    child2 = Todo(
        id="1.2",
        title="Child Task 2",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )

    verification1 = VerificationItem(
        id="v1",
        description="Run tests",
        input=CommandInput(type="command", command="pytest"),
        verify=NoneVerify(type="none"),
        completed=False,
    )
    verification2 = VerificationItem(
        id="v2",
        description="Check lint",
        input=CommandInput(type="command", command="ruff check"),
        verify=NoneVerify(type="none"),
        completed=False,
    )

    parent_task = Todo(
        id="1",
        title="Parent Task",
        status=TodoStatus.in_progress,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        children=[child1, child2],
        verification_spec=[verification1, verification2],
    )

    initial_plan = WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=None),
            progress=Progress(total_tasks=3, completed=0, in_progress=1, pending=2),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=[parent_task],
        success_vision=SuccessVision(),
        final_verification=[],
    )

    loader = PlanLoader(yaml_file)
    loader.save(initial_plan)

    # when - Step 1: Load YAML
    plan = loader.load()
    navigator = PlanNavigator(plan)

    # when - Step 2: Query task with filtering
    children = navigator.get_task_children("1")
    verifications = navigator.get_task_verification("1")

    # then - Step 2: Verify filtering works
    assert len(children) == 2
    assert children[0].id == "1.1"
    assert children[1].id == "1.2"
    assert len(verifications) == 2
    assert verifications[0].id == "v1"
    assert verifications[1].id == "v2"

    # when - Step 3: Mark verification item complete
    updated_verifications = [
        v.model_copy(update={"completed": True}) if v.id == "v1" else v for v in plan.todos[0].verification_spec
    ]
    updated_task = plan.todos[0].model_copy(update={"verification_spec": updated_verifications})
    plan = plan.model_copy(update={"todos": [updated_task]})
    loader.save(plan)

    # when - Step 4: Check completion (should be incomplete)
    plan = loader.load()
    navigator = PlanNavigator(plan)
    report1 = navigator.check_task_completion("1")

    # then - Step 4: Verify task cannot complete (children pending)
    assert report1.all_children_completed is False
    assert report1.all_verifications_completed is False
    assert report1.verification_summary["completed"] == 1
    assert report1.verification_summary["total"] == 2
    assert report1.can_complete is False

    # when - Step 5: Mark all child tasks complete
    def update_children_status(todos: list[Todo]) -> list[Todo]:
        result = []
        for todo in todos:
            if todo.id in ["1.1", "1.2"]:
                updated = todo.model_copy(update={"status": TodoStatus.completed})
                result.append(updated)
            else:
                updated_children = update_children_status(todo.children) if todo.children else []
                result.append(todo.model_copy(update={"children": updated_children}))
        return result

    updated_todos = update_children_status(plan.todos)
    plan = plan.model_copy(update={"todos": updated_todos})
    loader.save(plan)

    # when - Step 6: Mark remaining verification complete
    plan = loader.load()
    updated_verifications_final = [v.model_copy(update={"completed": True}) for v in plan.todos[0].verification_spec]
    updated_task_final = plan.todos[0].model_copy(update={"verification_spec": updated_verifications_final})
    plan = plan.model_copy(update={"todos": [updated_task_final]})
    loader.save(plan)

    # when - Step 7: Check completion again (should be complete)
    plan = loader.load()
    navigator = PlanNavigator(plan)
    report2 = navigator.check_task_completion("1")

    # then - Step 7: Verify task can now complete
    assert report2.all_children_completed is True
    assert report2.all_verifications_completed is True
    assert report2.verification_summary["completed"] == 2
    assert report2.verification_summary["total"] == 2
    assert report2.can_complete is True

    # when - Step 8: Save YAML and reload
    loader.save(plan)
    final_reloaded = loader.load()

    # then - Step 8: Verify data persisted correctly
    assert len(final_reloaded.todos) == 1
    assert final_reloaded.todos[0].id == "1"
    assert len(final_reloaded.todos[0].children) == 2
    assert final_reloaded.todos[0].children[0].status == TodoStatus.completed
    assert final_reloaded.todos[0].children[1].status == TodoStatus.completed
    assert len(final_reloaded.todos[0].verification_spec) == 2
    assert final_reloaded.todos[0].verification_spec[0].completed is True
    assert final_reloaded.todos[0].verification_spec[1].completed is True


async def test_empty_children_and_verification__when_leaf_task__handles_gracefully(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "leaf_task.yaml"

    leaf_task = Todo(
        id="1",
        title="Leaf Task",
        status=TodoStatus.in_progress,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        children=[],
        verification_spec=[],
    )

    plan = WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=None),
            progress=Progress(total_tasks=1, completed=0, in_progress=1, pending=0),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=[leaf_task],
        success_vision=SuccessVision(),
        final_verification=[],
    )

    loader = PlanLoader(yaml_file)
    loader.save(plan)

    # when
    loaded_plan = loader.load()
    navigator = PlanNavigator(loaded_plan)

    children = navigator.get_task_children("1")
    verifications = navigator.get_task_verification("1")
    descendants = navigator.get_all_descendants("1")
    report = navigator.check_task_completion("1")

    # then
    assert len(children) == 0
    assert len(verifications) == 0
    assert len(descendants) == 0
    assert report.all_children_completed is True
    assert report.all_verifications_completed is True
    assert report.can_complete is True


async def test_nonexistent_task_id__when_querying__raises_value_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "simple.yaml"

    task = Todo(
        id="1",
        title="Task",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )

    plan = WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=None),
            progress=Progress(total_tasks=1, completed=0, in_progress=0, pending=1),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=[task],
        success_vision=SuccessVision(),
        final_verification=[],
    )

    loader = PlanLoader(yaml_file)
    loader.save(plan)
    loaded_plan = loader.load()
    navigator = PlanNavigator(loaded_plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_task_children("999")

    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_task_verification("999")

    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_all_descendants("999")

    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.check_task_completion("999")


async def test_recursive_update_deduplication__when_updating_same_task_twice__applies_once(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "dedup_test.yaml"

    grandchild = Todo(
        id="1.1.1",
        title="Grandchild",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
    )
    child = Todo(
        id="1.1",
        title="Child",
        status=TodoStatus.pending,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        children=[grandchild],
    )
    parent = Todo(
        id="1",
        title="Parent",
        status=TodoStatus.in_progress,
        created_at="2025-01-01",
        updated_at="2025-01-01",
        children=[child],
    )

    plan = WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=None),
            progress=Progress(total_tasks=3, completed=0, in_progress=1, pending=2),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=[parent],
        success_vision=SuccessVision(),
        final_verification=[],
    )

    loader = PlanLoader(yaml_file)
    loader.save(plan)

    # when
    loaded_plan = loader.load()
    navigator = PlanNavigator(loaded_plan)
    descendants = navigator.get_all_descendants("1")
    task_ids_to_update = ["1"] + [d.id for d in descendants]

    # then
    assert task_ids_to_update == ["1", "1.1", "1.1.1"]
    assert len(set(task_ids_to_update)) == len(task_ids_to_update)
