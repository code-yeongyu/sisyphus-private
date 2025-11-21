"""Test automatic mark_plan_completed_if_all_done functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaItem,
    Background,
    BashVerification,
    ExecutionStatus,
    Metadata,
    Objectives,
    PlanDocument,
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
from sisyphus_core.core.plans.operations import mark_plan_completed_if_all_done

pytestmark = [pytest.mark.anyio]


def _create_user_request() -> UserRequest:
    """Helper to create UserRequest."""
    return UserRequest(original="test", created_at="2025-11-21T10:00:00Z", additional=[])


def _create_objectives() -> Objectives:
    """Helper to create Objectives."""
    return Objectives(core="test", detailed=[])


def _create_background() -> Background:
    """Helper to create Background."""
    return Background(
        current_situation="test",
        reason_for_change="test",
        changes_to_make="test",
    )


def _create_required_background() -> RequiredBackground:
    """Helper to create RequiredBackground."""
    return RequiredBackground(description="test", file_structure="test", references=[])


def _create_workflow() -> Workflow:
    """Helper to create Workflow."""
    return Workflow(dependency_diagram="test", critical_path=[])


def _create_success_vision() -> SuccessVision:
    """Helper to create SuccessVision."""
    return SuccessVision(
        user_perspective=[],
        business_perspective=[],
        technical_criteria=[],
    )


def _create_todo_completed(todo_id: str) -> Todo:
    """Helper to create completed todo with verification spec."""
    criterion1 = AcceptanceCriteriaItem(
        id=f"{todo_id}-criterion-1",
        condition="Acceptance criterion 1",
        verified_at="2025-11-21T10:00:00Z",
        verification_evidence="Verified",
    )
    criterion2 = AcceptanceCriteriaItem(
        id=f"{todo_id}-criterion-2",
        condition="Acceptance criterion 2",
        verified_at="2025-11-21T10:00:00Z",
        verification_evidence="Verified",
    )
    verification1 = VerificationItem(
        id=f"{todo_id}-verify-1",
        title="Verification 1",
        description="Test verification",
        verified=True,
        verified_at="2025-11-21T10:00:00Z",
        verification_evidence="Verified",
        orchestrator_manually_verified=True,
        manual_verification_evidence="Manually verified",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
    )
    verification2 = VerificationItem(
        id=f"{todo_id}-verify-2",
        title="Verification 2",
        description="Test verification",
        verified=True,
        verified_at="2025-11-21T10:00:00Z",
        verification_evidence="Verified",
        orchestrator_manually_verified=True,
        manual_verification_evidence="Manually verified",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
    )
    return Todo(
        id=todo_id,
        title=f"Completed Todo {todo_id}",
        status=TodoStatus.completed,
        acceptance_criteria=[criterion1, criterion2],
        verification_spec=[verification1, verification2],
    )


def _create_todo_pending(todo_id: str) -> Todo:
    """Create a pending todo."""
    criterion1 = AcceptanceCriteriaItem(
        id=f"{todo_id}-criterion-1",
        condition="Acceptance criterion 1",
    )
    criterion2 = AcceptanceCriteriaItem(
        id=f"{todo_id}-criterion-2",
        condition="Acceptance criterion 2",
    )
    return Todo(
        id=todo_id,
        title=f"Pending Todo {todo_id}",
        status=TodoStatus.pending,
        acceptance_criteria=[criterion1, criterion2],
    )


def _create_work_plan(
    plan_id: str,
    todos: list[Todo],
    completed: bool = False,
) -> WorkPlan:
    """Helper to create WorkPlan with given todos."""
    return WorkPlan(
        id=plan_id,
        name=f"Test Plan {plan_id}",
        user_request=_create_user_request(),
        objectives=_create_objectives(),
        background=_create_background(),
        required_background=_create_required_background(),
        workflow=_create_workflow(),
        success_vision=_create_success_vision(),
        final_verification=[],
        todos=todos,
        execution=ExecutionStatus(
            started=False,
            completed=completed,
            started_at=None,
            completed_at=None,
        ),
        work_mode=WorkMode(parallel_requested=False),
        acceptance_criteria_for_verification_agent=[],
    )


async def test_mark_completed_when_all_todos_done(tmp_path: Path) -> None:
    """
    Given: Plan with all todos completed
    When: mark_plan_completed_if_all_done is called
    Then: execution.completed = True and completed_at is set
    """
    # Given: Plan with all todos completed
    plan_path = tmp_path / "test_all_completed.yaml"
    todo1 = _create_todo_completed("1")
    todo2 = _create_todo_completed("2")
    work_plan = _create_work_plan("plan-1", [todo1, todo2])
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[work_plan],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: completed = True and completed_at is set
    assert result is True
    plan_doc_loaded = await load_plan(plan_path)
    assert plan_doc_loaded.work_plans[0].execution.completed is True
    assert plan_doc_loaded.work_plans[0].execution.completed_at is not None


async def test_mark_not_completed_when_todos_incomplete(tmp_path: Path) -> None:
    """
    Given: Plan with some todos that have unverified verification_spec
    When: mark_plan_completed_if_all_done is called
    Then: execution.completed remains False
    """
    # Given: Plan with todo having unverified verification items
    plan_path = tmp_path / "test_incomplete.yaml"
    todo1 = _create_todo_completed("1")
    unverified_verification = VerificationItem(
        id="2-verify-1",
        title="Unverified Verification",
        description="Test verification",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
    )
    todo2 = Todo(
        id="2",
        title="Todo with Unverified Verification",
        status=TodoStatus.completed,
        acceptance_criteria=[],
        verification_spec=[unverified_verification],
    )
    work_plan = _create_work_plan("plan-1", [todo1, todo2])
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[work_plan],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: completed remains False (one todo has unverified items)
    assert result is False
    plan_doc_loaded = await load_plan(plan_path)
    assert plan_doc_loaded.work_plans[0].execution.completed is False
    assert plan_doc_loaded.work_plans[0].execution.completed_at is None


async def test_mark_completed_with_empty_todos(tmp_path: Path) -> None:
    """
    Given: Plan with no todos (empty todos list treated as all completed)
    When: mark_plan_completed_if_all_done is called
    Then: Function returns True (empty list = all done)
    """
    # Given: Plan with no todos (empty todos list is valid complete state)
    plan_path = tmp_path / "test_empty_todos.yaml"
    work_plan = _create_work_plan("plan-1", [])
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[work_plan],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: Returns True (empty todos list means nothing to complete)
    assert result is True
    plan_doc_loaded = await load_plan(plan_path)
    assert plan_doc_loaded.work_plans[0].execution.completed is True
    assert plan_doc_loaded.work_plans[0].execution.completed_at is not None


async def test_mark_completed_with_no_work_plans(tmp_path: Path) -> None:
    """
    Given: Plan document with no work_plans
    When: mark_plan_completed_if_all_done is called
    Then: Function returns False gracefully
    """
    # Given: Plan document with empty work_plans list
    plan_path = tmp_path / "test_no_workplans.yaml"
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: Returns False gracefully
    assert result is False


async def test_mark_completed_when_file_not_found() -> None:
    """
    Given: Non-existent plan file
    When: mark_plan_completed_if_all_done is called
    Then: Function returns False without raising exception
    """
    # Given: Non-existent file path
    plan_path = Path("/nonexistent/path/plan.yaml")

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: Returns False without raising exception (graceful handling)
    assert result is False


async def test_mark_completed_with_multiple_todos_all_done(tmp_path: Path) -> None:
    """
    Given: Plan with multiple todos all completed
    When: mark_plan_completed_if_all_done is called
    Then: execution.completed = True
    """
    # Given: Plan with 3 completed todos
    plan_path = tmp_path / "test_multiple_todos.yaml"
    todos = [
        _create_todo_completed("1"),
        _create_todo_completed("2"),
        _create_todo_completed("3"),
    ]
    work_plan = _create_work_plan("plan-1", todos)
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[work_plan],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: completed = True
    assert result is True
    plan_doc_loaded = await load_plan(plan_path)
    assert plan_doc_loaded.work_plans[0].execution.completed is True


async def test_mark_completed_with_in_progress_todo(tmp_path: Path) -> None:
    """
    Given: Plan with one in_progress todo (status=in_progress means can_complete=False)
    When: mark_plan_completed_if_all_done is called
    Then: execution.completed remains False (in_progress blocks completion)
    """
    # Given: Plan with in_progress todo (status=in_progress always means can_complete=False)
    plan_path = tmp_path / "test_in_progress.yaml"
    todo1 = _create_todo_completed("1")
    unverified_verification = VerificationItem(
        id="2-verify-1",
        title="Unverified",
        description="Test",
        verified=False,
        orchestrator_manually_verified=False,
        manual_verification_evidence="",
        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
    )
    todo_in_progress = Todo(
        id="2",
        title="In Progress Todo",
        status=TodoStatus.in_progress,
        acceptance_criteria=[],
        verification_spec=[unverified_verification],
    )
    work_plan = _create_work_plan("plan-1", [todo1, todo_in_progress])
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[work_plan],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: completed remains False (in_progress status means cannot complete)
    assert result is False
    plan_doc_loaded = await load_plan(plan_path)
    assert plan_doc_loaded.work_plans[0].execution.completed is False


async def test_mark_completed_preserves_existing_data(tmp_path: Path) -> None:
    """
    Given: Plan with completed todos and other metadata
    When: mark_plan_completed_if_all_done is called
    Then: All other data is preserved
    """
    # Given: Plan with metadata
    plan_path = tmp_path / "test_preserve_data.yaml"
    todo1 = _create_todo_completed("1")
    work_plan = _create_work_plan("plan-1", [todo1])
    original_name = work_plan.name
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at="2025-11-21T10:00:00Z"),
        work_plans=[work_plan],
    )
    await save_plan(plan_path, plan_doc)

    # When: mark_plan_completed_if_all_done is called
    result = await mark_plan_completed_if_all_done(plan_path)

    # Then: Data is preserved
    assert result is True
    plan_doc_loaded = await load_plan(plan_path)
    assert plan_doc_loaded.work_plans[0].name == original_name
    assert plan_doc_loaded.work_plans[0].id == "plan-1"
    assert len(plan_doc_loaded.work_plans[0].todos) == 1
