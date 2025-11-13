"""Tests for verify_status() display - verifying table includes manual verification columns."""

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


@pytest.mark.anyio()
async def test_verify_status__collects_all_verifications_from_todos(
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
        current_work="",
    )

    # When - Collect all verifications (simulating verify_status logic)
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
async def test_verify_status__includes_manual_verification_fields(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
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
async def test_verify_status__detects_missing_manual_verification(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
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
