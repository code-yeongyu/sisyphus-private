"""Tests for continue_work() error messages - verifying CompletionReport behavior."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sisyphus_core.core.plans.models import (
    Background,
    BashVerification,
    ExecutionStatus,
    LLMJudgeBy,
    LLMJudgeVerification,
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
from sisyphus_core.core.task_manager import TaskManager


@pytest.mark.anyio()
async def test_continue_work__if_manual_incomplete__error_mentions_manual_verification(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """
    Given: A task with manual verification incomplete (orchestrator_manually_verified=False)
    When: check_task_completion() is called
    Then: CompletionReport indicates manual verification incomplete
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
                title="Test Task",
                description="Test",
                status=TodoStatus.in_progress,
                references=[],
                children=[],
                verification_spec=[
                    VerificationItem(
                        id="verify-1",
                        title="Test Manual Verification",
                        description="Test",
                        verified=True,
                        verified_at=None,
                        orchestrator_manually_verified=False,
                        manual_verification_evidence="",
                        bash=[],
                        llm_judge=[
                            LLMJudgeVerification(
                                by=LLMJudgeBy.ORCHESTRATOR, context_commands=[], instruction="Test instruction"
                            )
                        ],
                    )
                ],
            )
        ],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
        current_work="",
    )
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at=datetime.now(ZoneInfo("UTC")).isoformat()),
        work_plans=[work_plan],
    )
    task_manager = TaskManager(plan_doc, "test-plan")
    task = work_plan.todos[0]

    # When
    report = task_manager.check_task_completion(task.id)

    # Then
    assert report.can_complete is False, "Should not be able to complete with manual incomplete"
    assert report.all_manual_verifications_completed is False, "Manual verifications should be incomplete"
    assert report.manual_verification_summary["completed"] == 0, "Should have 0 manual verifications complete"
    assert report.manual_verification_summary["total"] == 1, "Should have 1 total verification"


@pytest.mark.anyio()
async def test_continue_work__if_all_verifications_incomplete__report_shows_counts(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """
    Given: A task with NO verifications complete
    When: check_task_completion() is called
    Then: CompletionReport shows 0/N for all verification types
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
                title="Test Task",
                description="Test",
                status=TodoStatus.in_progress,
                references=[],
                children=[],
                verification_spec=[
                    VerificationItem(
                        id="verify-1",
                        title="Bash Verification",
                        description="Test",
                        verified=False,
                        verified_at=None,
                        orchestrator_manually_verified=False,
                        manual_verification_evidence="",
                        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                        llm_judge=[],
                    ),
                    VerificationItem(
                        id="verify-2",
                        title="Manual Verification",
                        description="Test",
                        verified=False,
                        verified_at=None,
                        orchestrator_manually_verified=False,
                        manual_verification_evidence="",
                        bash=[],
                        llm_judge=[
                            LLMJudgeVerification(by=LLMJudgeBy.ORCHESTRATOR, context_commands=[], instruction="Test")
                        ],
                    ),
                ],
            )
        ],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
        current_work="",
    )
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at=datetime.now(ZoneInfo("UTC")).isoformat()),
        work_plans=[work_plan],
    )
    task_manager = TaskManager(plan_doc, "test-plan")
    task = work_plan.todos[0]

    # When
    report = task_manager.check_task_completion(task.id)

    # Then
    assert report.verification_summary["completed"] == 0
    assert report.verification_summary["total"] == 2
    assert report.manual_verification_summary["completed"] == 0
    assert report.manual_verification_summary["total"] == 2


@pytest.mark.anyio()
async def test_continue_work__if_mixed_state__report_shows_breakdown(
    minimal_user_request: UserRequest,
    minimal_objectives: Objectives,
    minimal_background: Background,
    minimal_required_background: RequiredBackground,
    minimal_workflow: Workflow,
    minimal_success_vision: SuccessVision,
) -> None:
    """
    Given: A task with mixed verification states (1 complete, 1 incomplete)
    When: check_task_completion() is called
    Then: CompletionReport shows accurate breakdown (1/2 verified, 1/2 manual)
    """
    # Given
    evidence_text = (
        "Complete evidence with more than 100 characters to satisfy "
        "the validation requirement for thorough verification documentation."
    )
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
                title="Test Task",
                description="Test",
                status=TodoStatus.in_progress,
                references=[],
                children=[],
                verification_spec=[
                    VerificationItem(
                        id="verify-1",
                        title="Complete Verification",
                        description="Test",
                        verified=True,
                        verified_at=datetime.now(ZoneInfo("UTC")).isoformat(),
                        orchestrator_manually_verified=True,
                        manual_verification_evidence=evidence_text,
                        bash=[BashVerification(execute="echo test", expected_exit_code=0)],
                        llm_judge=[],
                    ),
                    VerificationItem(
                        id="verify-2",
                        title="Incomplete Manual Verification",
                        description="Test",
                        verified=False,
                        verified_at=None,
                        orchestrator_manually_verified=False,
                        manual_verification_evidence="",
                        bash=[],
                        llm_judge=[
                            LLMJudgeVerification(by=LLMJudgeBy.ORCHESTRATOR, context_commands=[], instruction="Test")
                        ],
                    ),
                ],
            )
        ],
        references=[],
        execution=ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None),
        work_mode=WorkMode(parallel_requested=False),
        current_work="",
    )
    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at=datetime.now(ZoneInfo("UTC")).isoformat()),
        work_plans=[work_plan],
    )
    task_manager = TaskManager(plan_doc, "test-plan")
    task = work_plan.todos[0]

    # When
    report = task_manager.check_task_completion(task.id)

    # Then - Verification breakdown
    assert report.verification_summary["completed"] == 1, "Should have 1 verified"
    assert report.verification_summary["total"] == 2, "Should have 2 total"
    assert report.manual_verification_summary["completed"] == 1, "Should have 1 manual complete"
    assert report.manual_verification_summary["total"] == 2, "Should have 2 total manual"
    assert report.can_complete is False, "Should not complete with mixed state"
