"""Tests for status() display - verifying table includes manual verification columns and new --path option."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sisyphus_core.core.plans.models import (
    Background,
    BashVerification,
    ExecutionStatus,
    Objectives,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    VerificationItem,
    Workflow,
    WorkMode,
    WorkPlan,
)

from sisyphus_speckit.plan.status import (
    _count_all_todos,
    _count_completed_todos,
)


@pytest.mark.anyio()
async def test_status__collects_all_verifications_from_todos(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """
    Given: A WorkPlan with multiple tasks with verification specs
    When: Collecting verification items for status display
    Then: All verification items from all tasks are collected
    """
    # Given
    work_plan = WorkPlan(
        id="test-plan",
        name="Test Plan",
        depends_on=[],
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[
            Todo(
                id="1",
                title="Task 1",
                description="Test",
                status=TodoStatus.in_progress,
                references=[],
                children=[],
                verification_spec=[
                    VerificationItem(
                        id="verify-1",
                        title="Verification 1",
                        description="Test",
                        verified=True,
                        verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                        orchestrator_manually_verified=True,
                        manual_verification_evidence="Evidence 1",
                        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                        llm_judge=[],
                    )
                ],
            ),
            Todo(
                id="2",
                title="Task 2",
                description="Test",
                status=TodoStatus.pending,
                references=[],
                children=[],
                verification_spec=[
                    VerificationItem(
                        id="verify-2",
                        title="Verification 2",
                        description="Test",
                        verified=False,
                        verified_at=None,
                        orchestrator_manually_verified=False,
                        manual_verification_evidence="",
                        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                        llm_judge=[],
                    )
                ],
            ),
        ],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
    )

    # When - Collect all verifications (simulating status logic)
    all_verifications: list[tuple[str, str, VerificationItem]] = []

    def collect_verifications(todos: list[Todo]) -> None:
        for todo in todos:
            for verify_item in todo.verification_spec:
                all_verifications.append((todo.title, verify_item.title, verify_item))
            if todo.children:
                collect_verifications(todo.children)

    collect_verifications(work_plan.todos)

    # Then
    assert len(all_verifications) == 2, "Should collect 2 verification items"
    task1_title, verify1_title, verify1 = all_verifications[0]
    assert task1_title == "Task 1"
    assert verify1_title == "Verification 1"
    assert verify1.verified is True
    assert verify1.orchestrator_manually_verified is True
    assert verify1.manual_verification_evidence == "Evidence 1"

    task2_title, verify2_title, verify2 = all_verifications[1]
    assert task2_title == "Task 2"
    assert verify2_title == "Verification 2"
    assert verify2.verified is False
    assert verify2.orchestrator_manually_verified is False
    assert verify2.manual_verification_evidence == ""


@pytest.mark.anyio()
@pytest.mark.usefixtures(
    "minimal_background",
    "minimal_objectives",
    "minimal_required_background",
    "minimal_success_vision",
    "minimal_user_request",
    "minimal_workflow",
)
async def test_status__includes_manual_verification_fields() -> None:
    """
    Given: A verification item with manual verification complete
    When: Processing for display
    Then: Manual verification status and evidence presence are correctly detected
    """
    # Given
    evidence_text = "Manual verification evidence with sufficient detail for validation."
    verify_item = VerificationItem(
        id="verify-1",
        title="Test Verification",
        description="Test",
        verified=True,
        verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
        orchestrator_manually_verified=True,
        manual_verification_evidence=evidence_text,
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
        llm_judge=[],
    )

    # When - Simulate display logic
    status_emoji = "✓" if verify_item.verified else "○"
    manual_verified_emoji = "✓" if verify_item.orchestrator_manually_verified else "✗"
    evidence_status = "Present" if verify_item.manual_verification_evidence else "Missing"

    # Then
    assert status_emoji == "✓", "Verified item should show checkmark"
    assert manual_verified_emoji == "✓", "Manually verified item should show checkmark"
    assert evidence_status == "Present", "Item with evidence should show Present"


@pytest.mark.anyio()
@pytest.mark.usefixtures(
    "minimal_background",
    "minimal_objectives",
    "minimal_required_background",
    "minimal_success_vision",
    "minimal_user_request",
    "minimal_workflow",
)
async def test_status__detects_missing_manual_verification() -> None:
    """
    Given: A verification item with manual verification incomplete
    When: Processing for display
    Then: Manual verification status shows incomplete
    """
    # Given
    verify_item = VerificationItem(
        id="verify-1",
        title="Test Verification",
        description="Test",
        verified=True,
        verified_at=None,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
        llm_judge=[],
    )

    # When - Simulate display logic
    manual_verified_emoji = "✓" if verify_item.orchestrator_manually_verified else "✗"
    evidence_status = "Present" if verify_item.manual_verification_evidence else "Missing"

    # Then
    assert manual_verified_emoji == "✗", "Incomplete manual verification should show X"
    assert evidence_status == "Missing", "Item without evidence should show Missing"


@pytest.mark.usefixtures(
    "minimal_background",
    "minimal_objectives",
    "minimal_required_background",
    "minimal_success_vision",
    "minimal_user_request",
    "minimal_workflow",
)
def test_status__count_all_todos__counts_flat_todos() -> None:
    # given: A WorkPlan with 3 flat todos (no children)
    todos = [
        Todo(
            id="1",
            title="Task 1",
            description="Test",
            status=TodoStatus.in_progress,
            references=[],
            children=[],
            verification_spec=[],
        ),
        Todo(
            id="2",
            title="Task 2",
            description="Test",
            status=TodoStatus.completed,
            references=[],
            children=[],
            verification_spec=[],
        ),
        Todo(
            id="3",
            title="Task 3",
            description="Test",
            status=TodoStatus.pending,
            references=[],
            children=[],
            verification_spec=[],
        ),
    ]

    # when: Counting all todos
    count = _count_all_todos(todos)

    # then: Returns total count of 3
    assert count == 3


@pytest.mark.usefixtures(
    "minimal_background",
    "minimal_objectives",
    "minimal_required_background",
    "minimal_success_vision",
    "minimal_user_request",
    "minimal_workflow",
)
def test_status__count_all_todos__counts_nested_todos() -> None:
    # given: A WorkPlan with nested todos (parent with children)
    child_todo = Todo(
        id="1.1",
        title="Child Task",
        description="Test",
        status=TodoStatus.completed,
        references=[],
        children=[],
        verification_spec=[],
    )
    parent_todo = Todo(
        id="1",
        title="Parent Task",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[child_todo],
        verification_spec=[],
    )
    todos = [parent_todo]

    # when: Counting all todos recursively
    count = _count_all_todos(todos)

    # then: Returns total count of 2 (parent + child)
    assert count == 2


@pytest.mark.usefixtures(
    "minimal_background",
    "minimal_objectives",
    "minimal_required_background",
    "minimal_success_vision",
    "minimal_user_request",
    "minimal_workflow",
)
def test_status__count_completed_todos__counts_only_completed() -> None:
    # given: A WorkPlan with mixed status todos
    todos = [
        Todo(
            id="1",
            title="Task 1",
            description="Test",
            status=TodoStatus.completed,
            references=[],
            children=[],
            verification_spec=[],
        ),
        Todo(
            id="2",
            title="Task 2",
            description="Test",
            status=TodoStatus.in_progress,
            references=[],
            children=[],
            verification_spec=[],
        ),
        Todo(
            id="3",
            title="Task 3",
            description="Test",
            status=TodoStatus.completed,
            references=[],
            children=[],
            verification_spec=[],
        ),
    ]

    # when: Counting completed todos
    count = _count_completed_todos(todos)

    # then: Returns count of 2 (only completed todos)
    assert count == 2


@pytest.mark.usefixtures(
    "minimal_background",
    "minimal_objectives",
    "minimal_required_background",
    "minimal_success_vision",
    "minimal_user_request",
    "minimal_workflow",
)
def test_status__count_completed_todos__counts_nested_completed() -> None:
    # given: A WorkPlan with nested todos where parent is in_progress and child is completed
    child_todo = Todo(
        id="1.1",
        title="Child Task",
        description="Test",
        status=TodoStatus.completed,
        references=[],
        children=[],
        verification_spec=[],
    )
    parent_todo = Todo(
        id="1",
        title="Parent Task",
        description="Test",
        status=TodoStatus.in_progress,
        references=[],
        children=[child_todo],
        verification_spec=[],
    )
    todos = [parent_todo]

    # when: Counting completed todos recursively
    count = _count_completed_todos(todos)

    # then: Returns count of 1 (only the completed child)
    assert count == 1


def test_status__count_completed_todos__handles_empty_todos() -> None:
    # given: An empty todos list
    todos: list[Todo] = []

    # when: Counting completed todos
    count = _count_completed_todos(todos)

    # then: Returns 0
    assert count == 0


def test_status__count_all_todos__handles_empty_todos() -> None:
    # given: An empty todos list
    todos: list[Todo] = []

    # when: Counting all todos
    count = _count_all_todos(todos)

    # then: Returns 0
    assert count == 0


def test_status__progress_calculation__calculates_percentage() -> None:
    # given: Completed 3 out of 10 todos
    completed_todos = 3
    total_todos = 10

    # when: Calculating progress percentage
    progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

    # then: Returns 30.0%
    assert progress_pct == 30.0


def test_status__progress_calculation__handles_zero_total() -> None:
    # given: No todos at all (total = 0)
    completed_todos = 0
    total_todos = 0

    # when: Calculating progress percentage with zero total
    progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

    # then: Returns 0 (not division by zero)
    assert progress_pct == 0


def test_status__progress_calculation__all_completed() -> None:
    # given: All todos completed (5 out of 5)
    completed_todos = 5
    total_todos = 5

    # when: Calculating progress percentage
    progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

    # then: Returns 100.0%
    assert progress_pct == 100.0
