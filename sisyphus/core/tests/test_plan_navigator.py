import pytest

from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.utils.plan_types import (
    Background,
    ExecutionStatus,
    Metadata,
    Objectives,
    Progress,
    RequiredBackground,
    Status,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkMode,
    WorkPlan,
)

pytestmark = [pytest.mark.anyio]


def create_minimal_plan(
    todos: list[Todo],
    current_task_id: str | None = None,
) -> WorkPlan:
    return WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", timestamp="2025-01-01"),
        objectives=Objectives(core="Test"),
        background=Background(current_situation="A", reason_for_change="B", changes_to_make="C"),
        required_background=RequiredBackground(description="Test"),
        status=Status(
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id=current_task_id),
            progress=Progress(total_tasks=0, completed=0, in_progress=0, pending=0),
            current_work="None",
        ),
        workflow=Workflow(dependency_diagram="Test"),
        todos=todos,
        success_vision=SuccessVision(),
        final_verification=[],
    )


async def test_get_current_task__when_current_task_id_is_none__returns_none() -> None:
    # given
    plan = create_minimal_plan(todos=[], current_task_id=None)
    navigator = PlanNavigator(plan)

    # when
    current = navigator.get_current_task()

    # then
    assert current is None


async def test_get_current_task__when_current_task_id_is_set__returns_task() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Task 1",
            status=TodoStatus.in_progress,
            created_at="2025-01-01",
            updated_at="2025-01-01",
        )
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1")
    navigator = PlanNavigator(plan)

    # when
    current = navigator.get_current_task()

    # then
    assert current is not None
    assert current.id == "1"
    assert current.title == "Task 1"


async def test_get_next_task__when_no_current_task__returns_first_pending() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id=None)
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "1"


async def test_get_next_task__when_current_in_progress_with_children__returns_first_child() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Parent",
            status=TodoStatus.in_progress,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="1.1",
                    title="Child 1",
                    status=TodoStatus.pending,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
                Todo(
                    id="1.2",
                    title="Child 2",
                    status=TodoStatus.pending,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "1.1"


async def test_get_next_task__when_current_in_progress_no_children__returns_sibling() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.in_progress, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "2"


async def test_get_next_task__when_current_completed__returns_next_sibling() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.completed, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "2"


async def test_get_next_task__when_last_sibling_completed__backtracks_to_parent_sibling() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Parent 1",
            status=TodoStatus.completed,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="1.1",
                    title="Child 1.1",
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
                Todo(
                    id="1.2",
                    title="Child 1.2",
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        ),
        Todo(id="2", title="Parent 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1.2")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "2"


async def test_get_next_task__when_all_completed__returns_none() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.completed, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.completed, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="2")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is None


async def test_get_next_task__when_current_id_not_found__raises_value_error() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="999")
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_next_task()


async def test_find_todo_by_id__when_root_level__returns_task() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    found = navigator.find_todo_by_id("2")

    # then
    assert found is not None
    assert found.id == "2"
    assert found.title == "Task 2"


async def test_find_todo_by_id__when_nested__returns_task() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Parent",
            status=TodoStatus.pending,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="1.1",
                    title="Child",
                    status=TodoStatus.pending,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                    children=[
                        Todo(
                            id="1.1.1",
                            title="Grandchild",
                            status=TodoStatus.pending,
                            created_at="2025-01-01",
                            updated_at="2025-01-01",
                        ),
                    ],
                ),
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    found = navigator.find_todo_by_id("1.1.1")

    # then
    assert found is not None
    assert found.id == "1.1.1"
    assert found.title == "Grandchild"


async def test_find_todo_by_id__when_not_found__returns_none() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    found = navigator.find_todo_by_id("999")

    # then
    assert found is None


async def test_get_next_task__dfs_order__skips_completed_children() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Parent",
            status=TodoStatus.in_progress,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="1.1",
                    title="Child 1",
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
                Todo(
                    id="1.2",
                    title="Child 2",
                    status=TodoStatus.pending,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "1.2"


async def test_get_next_task__complex_tree_navigation() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Task 1",
            status=TodoStatus.completed,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="1.1",
                    title="Task 1.1",
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
                Todo(
                    id="1.2",
                    title="Task 1.2",
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        ),
        Todo(
            id="2",
            title="Task 2",
            status=TodoStatus.in_progress,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="2.1",
                    title="Task 2.1",
                    status=TodoStatus.pending,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        ),
        Todo(id="3", title="Task 3", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="2")
    navigator = PlanNavigator(plan)

    # when
    next_task = navigator.get_next_task()

    # then
    assert next_task is not None
    assert next_task.id == "2.1"
