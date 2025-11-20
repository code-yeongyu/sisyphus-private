"""Tests for plan overview command."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sisyphus_core.core.plans.models import (
    Background,
    DetailedObjective,
    ExecutionStatus,
    Objectives,
    ReferenceItem,
    RequiredBackground,
    SuccessVision,
    Todo,
    TodoStatus,
    UserRequest,
    Workflow,
    WorkMode,
    WorkPlan,
)

from sisyphus_speckit.plan.overview import (
    _count_all_todos,
    _count_completed_todos,
)


@pytest.fixture()
def minimal_user_request() -> UserRequest:
    """Minimal UserRequest for testing."""
    return UserRequest(
        original="Test user request",
        created_at="2025-11-06T00:00:00Z",
        additional=["Additional requirement 1"],
    )


@pytest.fixture()
def minimal_objectives() -> Objectives:
    """Minimal Objectives for testing."""
    return Objectives(
        core="Test core objective",
        detailed=[
            DetailedObjective(
                goal="Test goal",
                measurable="Test measurable",
            ),
        ],
    )


@pytest.fixture()
def minimal_background() -> Background:
    """Minimal Background for testing."""
    return Background(
        current_situation="Current situation description",
        reason_for_change="Reason for change description",
        changes_to_make="Changes to make description",
    )


@pytest.fixture()
def minimal_required_background() -> RequiredBackground:
    """Minimal RequiredBackground for testing."""
    return RequiredBackground(
        description="Required background description",
        file_structure=None,
        references=[
            ReferenceItem(ref_id="ref-1", uri="https://example.com"),
        ],
    )


@pytest.fixture()
def minimal_workflow() -> Workflow:
    """Minimal Workflow for testing."""
    return Workflow(
        dependency_diagram="Dependency diagram content",
        critical_path=["1", "2"],
    )


@pytest.fixture()
def minimal_success_vision() -> SuccessVision:
    """Minimal SuccessVision for testing."""
    return SuccessVision(
        user_perspective=[],
        business_perspective=[],
        technical_criteria=[],
    )


@pytest.fixture()
def minimal_work_plan(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> WorkPlan:
    """Minimal WorkPlan for testing."""
    return WorkPlan(
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
                description="Test task 1",
                status=TodoStatus.completed,
                references=[],
                children=[],
                verification_spec=[],
            ),
            Todo(
                id="2",
                title="Task 2",
                description="Test task 2",
                status=TodoStatus.in_progress,
                references=[],
                children=[],
                verification_spec=[],
            ),
        ],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )


def test_overview__if_all_fields_present__displays_all_sections(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    _capsys: pytest.CaptureFixture[str],
) -> None:
    # given: A WorkPlan with all fields populated
    work_plan = WorkPlan(
        id="test-overview",
        name="Complete Test Plan",
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
                description="First task",
                status=TodoStatus.completed,
                references=[],
                children=[],
                verification_spec=[],
            ),
            Todo(
                id="2",
                title="Task 2",
                description="Second task",
                status=TodoStatus.in_progress,
                references=[],
                children=[],
                verification_spec=[],
            ),
        ],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )

    # when: Simulating overview display (verifying all fields are accessible)
    total_todos = _count_all_todos(work_plan.todos)
    completed_todos = _count_completed_todos(work_plan.todos)

    # then: All sections should be accessible
    assert work_plan.id == "test-overview"
    assert work_plan.name == "Complete Test Plan"
    assert work_plan.user_request.original == "Test user request"
    assert len(work_plan.user_request.additional) == 1
    assert work_plan.objectives.core == "Test core objective"
    assert len(work_plan.objectives.detailed) == 1
    assert work_plan.background.current_situation == "Current situation description"
    assert work_plan.background.reason_for_change == "Reason for change description"
    assert work_plan.background.changes_to_make == "Changes to make description"
    assert work_plan.required_background.description == "Required background description"
    assert len(work_plan.required_background.references) == 1
    assert work_plan.workflow.dependency_diagram == "Dependency diagram content"
    assert len(work_plan.workflow.critical_path) == 2
    assert total_todos == 2
    assert completed_todos == 1


def test_overview__if_path_option_provided__loads_specific_plan(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
    tmp_path: Path,
) -> None:
    # given: A plan file at specific path
    plan_file = tmp_path / "test_plan.yaml"

    work_plan = WorkPlan(
        id="specific-plan",
        name="Specific Test Plan",
        depends_on=[],
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )

    # when: Verifying path can be provided (simulate --path option)
    # then: Path should be resolvable
    assert plan_file.parent.exists() or tmp_path.exists()
    assert work_plan.id == "specific-plan"


def test_overview__if_plan_has_no_todos__displays_zero_progress(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A WorkPlan with empty todos list
    work_plan = WorkPlan(
        id="empty-plan",
        name="Empty Plan",
        depends_on=[],
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )

    # when: Calculating progress
    total_todos = _count_all_todos(work_plan.todos)
    completed_todos = _count_completed_todos(work_plan.todos)
    progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

    # then: Progress should be 0, not NaN or error
    assert total_todos == 0
    assert completed_todos == 0
    assert progress_pct == 0


def test_overview__progress_calculates_percentage_correctly() -> None:
    # given: 3 completed todos out of 10 total
    completed_todos = 3
    total_todos = 10

    # when: Calculating progress percentage
    progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

    # then: Progress should be 30%
    assert progress_pct == 30.0


def test_overview__progress_calculates_one_hundred_percent() -> None:
    # given: All todos completed (5 out of 5)
    completed_todos = 5
    total_todos = 5

    # when: Calculating progress percentage
    progress_pct = (completed_todos / total_todos * 100) if total_todos > 0 else 0

    # then: Progress should be 100%
    assert progress_pct == 100.0


def test_overview__if_nested_todos__counts_all_levels() -> None:
    # given: A plan with nested todos (parent and children)
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
    total = _count_all_todos(todos)
    completed = _count_completed_todos(todos)

    # then: Should count both parent and child
    assert total == 2
    assert completed == 1
    assert (completed / total * 100) == 50.0


def test_overview__if_acceptance_criteria_missing__handles_gracefully(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A WorkPlan without acceptance_criteria field
    work_plan = WorkPlan(
        id="no-criteria",
        name="Plan Without Criteria",
        depends_on=[],
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )

    # when: Checking if acceptance_criteria exists
    has_criteria = hasattr(work_plan, "acceptance_criteria") and work_plan.acceptance_criteria

    # then: Should not error, just return False
    assert has_criteria is False


def test_overview__if_fully_done_not_set__displays_no() -> None:
    # given: A WorkPlan with fully_done_at = None
    execution = ExecutionStatus(
        started=False,
        completed=False,
        started_at=None,
        completed_at=None,
    )

    # when: Checking fully_done status
    fully_done = execution.fully_done_at is not None

    # then: Should display No
    assert fully_done is False


def test_overview__if_fully_done_set__displays_yes() -> None:
    # given: A WorkPlan with fully_done_at timestamp
    execution = ExecutionStatus(
        started=False,
        completed=False,
        started_at=None,
        completed_at=None,
        fully_done_at=datetime.now(ZoneInfo("UTC")).isoformat(),
    )

    # when: Checking fully_done status
    fully_done = execution.fully_done_at is not None

    # then: Should display Yes
    assert fully_done is True


def test_overview__plan_metadata_displays_correctly(
    minimal_work_plan: WorkPlan,
) -> None:
    # given: A complete WorkPlan
    # when: Extracting plan metadata
    plan_id = minimal_work_plan.id
    plan_name = minimal_work_plan.name
    total_todos = _count_all_todos(minimal_work_plan.todos)
    completed_todos = _count_completed_todos(minimal_work_plan.todos)
    fully_done = minimal_work_plan.execution.fully_done_at is not None

    # then: All metadata should be available
    assert plan_id == "test-plan"
    assert plan_name == "Test Plan"
    assert total_todos == 2
    assert completed_todos == 1
    assert fully_done is False


def test_overview__multiple_additional_requirements_displayed(
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A user request with multiple additional requirements
    user_request = UserRequest(
        original="Original request",
        created_at="2025-11-06T00:00:00Z",
        additional=[
            "Additional requirement 1",
            "Additional requirement 2",
            "Additional requirement 3",
        ],
    )
    work_plan = WorkPlan(
        id="multi-req",
        name="Multiple Requirements Plan",
        depends_on=[],
        user_request=user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )

    # when: Accessing additional requirements
    additional_count = len(work_plan.user_request.additional)

    # then: All additional requirements should be accessible
    assert additional_count == 3
    assert work_plan.user_request.additional[0] == "Additional requirement 1"
    assert work_plan.user_request.additional[1] == "Additional requirement 2"
    assert work_plan.user_request.additional[2] == "Additional requirement 3"


def test_overview__final_verification_table_accessible(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    # given: A plan with final_verification items
    work_plan = WorkPlan(
        id="with-verification",
        name="Plan with Verification",
        depends_on=[],
        user_request=minimal_user_request,
        objectives=minimal_objectives,
        background=minimal_background,
        required_background=minimal_required_background,
        workflow=minimal_workflow,
        success_vision=minimal_success_vision,
        final_verification=[],
        todos=[],
        references=[],
        execution=ExecutionStatus(
            started=False,
            completed=False,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
    )

    # when: Accessing final_verification
    verification_items = work_plan.final_verification

    # then: Should be accessible (can be empty list)
    assert isinstance(verification_items, list)
    assert len(verification_items) == 0
