import pytest

from sisyphus.core.plan_navigator import PlanNavigator
from sisyphus.utils.plan_types import (
    Background,
    BashVerification,
    ExecutionStatus,
    Metadata,
    Objectives,
    Progress,
    ReferencePointer,
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


def create_minimal_plan(
    todos: list[Todo],
    current_task_id: str | None = None,
) -> WorkPlan:
    return WorkPlan(
        metadata=Metadata(created_at="2025-01-01", updated_at="2025-01-01"),
        user_request=UserRequest(original="Test", created_at="2025-01-01"),
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


async def test_get_task_references__when_task_has_references__returns_references() -> None:
    # given

    todos = [
        Todo(
            id="1",
            title="Task 1",
            status=TodoStatus.pending,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            references=[
                ReferencePointer(type="pointer", ref_id="ref-1", notes="Reference 1"),  # type: ignore[arg-type]
                ReferencePointer(type="pointer", ref_id="ref-2", notes="Reference 2"),  # type: ignore[arg-type]
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    refs = navigator.get_task_references("1")

    # then
    assert len(refs) == 2
    assert refs[0].ref_id == "ref-1"
    assert refs[0].notes == "Reference 1"
    assert refs[1].ref_id == "ref-2"


async def test_get_task_references__when_task_not_found__raises_value_error() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_task_references("999")


async def test_get_task_children__when_task_has_children__returns_children() -> None:
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
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    children = navigator.get_task_children("1")

    # then
    assert len(children) == 2
    assert children[0].id == "1.1"
    assert children[0].title == "Child 1"
    assert children[1].id == "1.2"


async def test_get_task_children__when_task_has_no_children__returns_empty_list() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    children = navigator.get_task_children("1")

    # then
    assert len(children) == 0


async def test_get_task_children__when_task_not_found__raises_value_error() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_task_children("999")


async def test_get_all_descendants__when_nested_children__returns_all_recursively() -> None:
    # given - 1 -> 1.1 -> 1.1.1
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
    descendants = navigator.get_all_descendants("1")

    # then
    assert len(descendants) == 2
    assert descendants[0].id == "1.1"
    assert descendants[1].id == "1.1.1"


async def test_get_all_descendants__when_multiple_branches__returns_all() -> None:
    # given - 1 -> [1.1, 1.2], 1.1 -> [1.1.1]
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
                    title="Child 1",
                    status=TodoStatus.pending,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                    children=[
                        Todo(
                            id="1.1.1",
                            title="Grandchild 1.1",
                            status=TodoStatus.pending,
                            created_at="2025-01-01",
                            updated_at="2025-01-01",
                        ),
                    ],
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
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    descendants = navigator.get_all_descendants("1")

    # then
    assert len(descendants) == 3
    assert descendants[0].id == "1.1"
    assert descendants[1].id == "1.1.1"
    assert descendants[2].id == "1.2"


async def test_get_all_descendants__when_no_children__returns_empty_list() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    descendants = navigator.get_all_descendants("1")

    # then
    assert len(descendants) == 0


async def test_get_all_descendants__when_task_not_found__raises_value_error() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_all_descendants("999")


async def test_get_task_verification__when_task_has_verification__returns_verification() -> None:
    # given

    todos = [
        Todo(
            id="1",
            title="Task 1",
            status=TodoStatus.pending,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            verification_spec=[
                VerificationItem(
                    id="v1",
                    title="Verify test 1",
                    description="Verify test 1",
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test")],
                    verified=False,
                ),
                VerificationItem(
                    id="v2",
                    title="Verify test 2",
                    description="Verify test 2",
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test")],
                    verified=True,
                ),
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    verifications = navigator.get_task_verification("1")

    # then
    assert len(verifications) == 2
    assert verifications[0].id == "v1"
    assert verifications[0].verified is False
    assert verifications[1].id == "v2"
    assert verifications[1].verified is True


async def test_get_task_verification__when_no_verification__returns_empty_list() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    verifications = navigator.get_task_verification("1")

    # then
    assert len(verifications) == 0


async def test_get_task_verification__when_task_not_found__raises_value_error() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_task_verification("999")


async def test_check_task_completion__when_all_completed__returns_can_complete_true() -> None:
    # given - all children completed, all verifications completed
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
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
            verification_spec=[
                VerificationItem(
                    id="v1",
                    title="Test 1",
                    description="Test 1",
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test")],
                    verified=True,
                ),
                VerificationItem(
                    id="v2",
                    title="Test 2",
                    description="Test 2",
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test")],
                    verified=True,
                ),
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    report = navigator.check_task_completion("1")

    # then
    assert report.task_id == "1"
    assert report.task_status == TodoStatus.in_progress
    assert report.all_children_completed is True
    assert report.children_summary["completed"] == 2
    assert report.all_verifications_completed is True
    assert report.verification_summary["completed"] == 2
    assert report.verification_summary["total"] == 2
    assert report.can_complete is True


async def test_check_task_completion__when_children_pending__returns_can_complete_false() -> None:
    # given - some children pending
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
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    report = navigator.check_task_completion("1")

    # then
    assert report.all_children_completed is False
    assert report.children_summary["completed"] == 1
    assert report.children_summary["pending"] == 1
    assert report.can_complete is False


async def test_check_task_completion__when_verification_incomplete__returns_can_complete_false() -> None:
    # given - verifications not all completed
    todos = [
        Todo(
            id="1",
            title="Task",
            status=TodoStatus.in_progress,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            verification_spec=[
                VerificationItem(
                    id="v1",
                    title="Test 1",
                    description="Test 1",
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test")],
                    verified=True,
                ),
                VerificationItem(
                    id="v2",
                    title="Test 2",
                    description="Test 2",
                    orchestrator_manually_verified=False,
                    manual_verification_evidence="",
                    bash=[BashVerification(execute="echo test")],
                    verified=False,
                ),
            ],
        )
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    report = navigator.check_task_completion("1")

    # then
    assert report.all_verifications_completed is False
    assert report.verification_summary["completed"] == 1
    assert report.verification_summary["total"] == 2
    assert report.can_complete is False


async def test_check_task_completion__when_no_children_no_verification__returns_can_complete_true() -> None:
    # given - leaf task with no children and no verification
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.in_progress, created_at="2025-01-01", updated_at="2025-01-01")
    ]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when
    report = navigator.check_task_completion("1")

    # then
    assert report.all_children_completed is True
    assert report.all_verifications_completed is True
    assert report.can_complete is True


async def test_check_task_completion__when_task_not_found__raises_value_error() -> None:
    # given
    todos = [Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01")]
    plan = create_minimal_plan(todos=todos)
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.check_task_completion("999")


async def test_get_previous_task__if_current_none__returns_none() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id=None)
    navigator = PlanNavigator(plan)

    # when
    previous = navigator.get_previous_task()

    # then
    assert previous is None


async def test_get_previous_task__if_first_task__returns_none() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.in_progress, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1")
    navigator = PlanNavigator(plan)

    # when
    previous = navigator.get_previous_task()

    # then
    assert previous is None


async def test_get_previous_task__if_second_task__returns_first() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.completed, created_at="2025-01-01", updated_at="2025-01-01"),
        Todo(id="2", title="Task 2", status=TodoStatus.in_progress, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="2")
    navigator = PlanNavigator(plan)

    # when
    previous = navigator.get_previous_task()

    # then
    assert previous is not None
    assert previous.id == "1"


async def test_get_previous_task__if_first_child__returns_parent() -> None:
    # given
    todos = [
        Todo(
            id="1",
            title="Parent",
            status=TodoStatus.completed,
            created_at="2025-01-01",
            updated_at="2025-01-01",
            children=[
                Todo(
                    id="1.1",
                    title="Child 1",
                    status=TodoStatus.in_progress,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        ),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1.1")
    navigator = PlanNavigator(plan)

    # when
    previous = navigator.get_previous_task()

    # then
    assert previous is not None
    assert previous.id == "1"


async def test_get_previous_task__if_second_sibling__returns_last_descendant_of_first() -> None:
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
                    title="Child 1.1",
                    status=TodoStatus.completed,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                    children=[
                        Todo(
                            id="1.1.1",
                            title="Grandchild 1.1.1",
                            status=TodoStatus.completed,
                            created_at="2025-01-01",
                            updated_at="2025-01-01",
                        ),
                        Todo(
                            id="1.1.2",
                            title="Grandchild 1.1.2",
                            status=TodoStatus.completed,
                            created_at="2025-01-01",
                            updated_at="2025-01-01",
                        ),
                    ],
                ),
                Todo(
                    id="1.2",
                    title="Child 1.2",
                    status=TodoStatus.in_progress,
                    created_at="2025-01-01",
                    updated_at="2025-01-01",
                ),
            ],
        ),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="1.2")
    navigator = PlanNavigator(plan)

    # when
    previous = navigator.get_previous_task()

    # then
    assert previous is not None
    assert previous.id == "1.1.2"


async def test_get_previous_task__if_task_not_found__raises_value_error() -> None:
    # given
    todos = [
        Todo(id="1", title="Task 1", status=TodoStatus.pending, created_at="2025-01-01", updated_at="2025-01-01"),
    ]
    plan = create_minimal_plan(todos=todos, current_task_id="999")
    navigator = PlanNavigator(plan)

    # when & then
    with pytest.raises(ValueError, match="작업 ID를 찾을 수 없습니다: 999"):
        navigator.get_previous_task()
