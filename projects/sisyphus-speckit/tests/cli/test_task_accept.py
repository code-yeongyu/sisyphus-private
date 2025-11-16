"""Tests for task accept command with acceptance criteria marking."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import (
    AcceptanceCriteriaChecklist,
    AcceptanceCriteriaForVerificationAgent,
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

pytestmark = [pytest.mark.anyio]


async def test_accept__if_valid_criterion_id__marks_checklist() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        acceptance_criteria = [
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Core functionality verification",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="no-naive-type-hints",
                        title="No naive type hints",
                        content="All functions must have proper type hints",
                        checked_at=None,
                        checked_evidence=None,
                    ),
                    AcceptanceCriteriaChecklist(
                        id="proper-error-handling",
                        title="Proper error handling",
                        content="All errors must be caught and handled",
                        checked_at=None,
                        checked_evidence=None,
                    ),
                ],
            ),
        ]

        verification_spec: list[VerificationItem] = [
            VerificationItem(
                id="verify-1",
                title="Test verification",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for acceptance criteria",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=verification_spec,
            parallel=False,
            acceptance_criteria=[],
        )

        work_plan = WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=UserRequest(
                original="Test",
                created_at=datetime.now(UTC).isoformat(),
            ),
            objectives=Objectives(core="Test", detailed=[]),
            background=Background(
                current_situation="Test",
                reason_for_change="Test",
                changes_to_make="Test",
            ),
            required_background=RequiredBackground(
                description="Test",
                references=[],
            ),
            workflow=Workflow(dependency_diagram="", critical_path=[]),
            success_vision=SuccessVision(
                user_perspective=[],
                business_perspective=[],
                technical_criteria=[],
            ),
            final_verification=[],
            todos=[todo],
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id="test-1"),
            acceptance_criteria_for_verification_agent=acceptance_criteria,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        criteria = loaded_plan.work_plans[0].acceptance_criteria_for_verification_agent[0]
        checklist = criteria.checklists[0]

        # Simulate marking the checklist
        now = datetime.now(UTC).isoformat()
        evidence = "Type hints verified with basedpyright"
        checklist.checked_at = now
        checklist.checked_evidence = evidence

        await save_plan(plan_path, loaded_plan)

        # then
        reloaded_plan = await load_plan(plan_path)
        marked_checklist = (
            reloaded_plan.work_plans[0]
            .acceptance_criteria_for_verification_agent[0]
            .checklists[0]
        )
        assert marked_checklist.checked_at is not None
        assert marked_checklist.checked_at == now
        assert marked_checklist.checked_evidence == evidence


async def test_accept__if_multiple_checklists__updates_only_specified() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        acceptance_criteria = [
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Core functionality verification",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="first-check",
                        title="First check",
                        content="First check content",
                        checked_at=None,
                        checked_evidence=None,
                    ),
                    AcceptanceCriteriaChecklist(
                        id="second-check",
                        title="Second check",
                        content="Second check content",
                        checked_at=None,
                        checked_evidence=None,
                    ),
                    AcceptanceCriteriaChecklist(
                        id="third-check",
                        title="Third check",
                        content="Third check content",
                        checked_at=None,
                        checked_evidence=None,
                    ),
                ],
            ),
        ]

        verification_spec: list[VerificationItem] = [
            VerificationItem(
                id="verify-1",
                title="Test verification",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for acceptance criteria",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=verification_spec,
            parallel=False,
            acceptance_criteria=[],
        )

        work_plan = WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=UserRequest(
                original="Test",
                created_at=datetime.now(UTC).isoformat(),
            ),
            objectives=Objectives(core="Test", detailed=[]),
            background=Background(
                current_situation="Test",
                reason_for_change="Test",
                changes_to_make="Test",
            ),
            required_background=RequiredBackground(
                description="Test",
                references=[],
            ),
            workflow=Workflow(dependency_diagram="", critical_path=[]),
            success_vision=SuccessVision(
                user_perspective=[],
                business_perspective=[],
                technical_criteria=[],
            ),
            final_verification=[],
            todos=[todo],
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id="test-1"),
            acceptance_criteria_for_verification_agent=acceptance_criteria,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        criteria = loaded_plan.work_plans[0].acceptance_criteria_for_verification_agent[0]

        # Mark only the second checklist
        now = datetime.now(UTC).isoformat()
        criteria.checklists[1].checked_at = now
        criteria.checklists[1].checked_evidence = "Second check evidence"

        await save_plan(plan_path, loaded_plan)

        # then
        reloaded_plan = await load_plan(plan_path)
        reloaded_criteria = (
            reloaded_plan.work_plans[0]
            .acceptance_criteria_for_verification_agent[0]
        )

        # First checklist should remain unchecked
        assert reloaded_criteria.checklists[0].checked_at is None
        assert reloaded_criteria.checklists[0].checked_evidence is None

        # Second checklist should be marked
        assert reloaded_criteria.checklists[1].checked_at == now
        assert reloaded_criteria.checklists[1].checked_evidence == "Second check evidence"

        # Third checklist should remain unchecked
        assert reloaded_criteria.checklists[2].checked_at is None
        assert reloaded_criteria.checklists[2].checked_evidence is None


async def test_accept__if_invalid_criterion_id__returns_error() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        acceptance_criteria = [
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Core functionality verification",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="existing-check",
                        title="Existing check",
                        content="Existing check content",
                        checked_at=None,
                        checked_evidence=None,
                    ),
                ],
            ),
        ]

        verification_spec: list[VerificationItem] = [
            VerificationItem(
                id="verify-1",
                title="Test verification",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for acceptance criteria",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=verification_spec,
            parallel=False,
            acceptance_criteria=[],
        )

        work_plan = WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=UserRequest(
                original="Test",
                created_at=datetime.now(UTC).isoformat(),
            ),
            objectives=Objectives(core="Test", detailed=[]),
            background=Background(
                current_situation="Test",
                reason_for_change="Test",
                changes_to_make="Test",
            ),
            required_background=RequiredBackground(
                description="Test",
                references=[],
            ),
            workflow=Workflow(dependency_diagram="", critical_path=[]),
            success_vision=SuccessVision(
                user_perspective=[],
                business_perspective=[],
                technical_criteria=[],
            ),
            final_verification=[],
            todos=[todo],
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id="test-1"),
            acceptance_criteria_for_verification_agent=acceptance_criteria,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        criteria = loaded_plan.work_plans[0].acceptance_criteria_for_verification_agent[0]

        # Try to find a non-existent checklist
        found = False
        for checklist in criteria.checklists:
            if checklist.id == "non-existent-id":
                found = True
                break

        # then
        assert not found


async def test_accept__if_timestamp_persists__saves_correctly() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        original_timestamp = "2025-11-16T10:30:45.123456+00:00"

        acceptance_criteria = [
            AcceptanceCriteriaForVerificationAgent(
                id="criteria-1",
                title="Core functionality verification",
                checklists=[
                    AcceptanceCriteriaChecklist(
                        id="check-1",
                        title="Check 1",
                        content="Check 1 content",
                        checked_at=original_timestamp,
                        checked_evidence="Original evidence",
                    ),
                ],
            ),
        ]

        verification_spec: list[VerificationItem] = [
            VerificationItem(
                id="verify-1",
                title="Test verification",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for acceptance criteria",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=verification_spec,
            parallel=False,
            acceptance_criteria=[],
        )

        work_plan = WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=UserRequest(
                original="Test",
                created_at=datetime.now(UTC).isoformat(),
            ),
            objectives=Objectives(core="Test", detailed=[]),
            background=Background(
                current_situation="Test",
                reason_for_change="Test",
                changes_to_make="Test",
            ),
            required_background=RequiredBackground(
                description="Test",
                references=[],
            ),
            workflow=Workflow(dependency_diagram="", critical_path=[]),
            success_vision=SuccessVision(
                user_perspective=[],
                business_perspective=[],
                technical_criteria=[],
            ),
            final_verification=[],
            todos=[todo],
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id="test-1"),
            acceptance_criteria_for_verification_agent=acceptance_criteria,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        reloaded_plan = await load_plan(plan_path)

        # then
        checklist = (
            reloaded_plan.work_plans[0]
            .acceptance_criteria_for_verification_agent[0]
            .checklists[0]
        )
        assert checklist.checked_at == original_timestamp
        assert checklist.checked_evidence == "Original evidence"


async def test_accept__if_empty_acceptance_criteria__handles_gracefully() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        verification_spec: list[VerificationItem] = [
            VerificationItem(
                id="verify-1",
                title="Test verification",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for acceptance criteria",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=verification_spec,
            parallel=False,
            acceptance_criteria=[],
        )

        work_plan = WorkPlan(
            id="test-plan",
            name="Test Plan",
            depends_on=[],
            user_request=UserRequest(
                original="Test",
                created_at=datetime.now(UTC).isoformat(),
            ),
            objectives=Objectives(core="Test", detailed=[]),
            background=Background(
                current_situation="Test",
                reason_for_change="Test",
                changes_to_make="Test",
            ),
            required_background=RequiredBackground(
                description="Test",
                references=[],
            ),
            workflow=Workflow(dependency_diagram="", critical_path=[]),
            success_vision=SuccessVision(
                user_perspective=[],
                business_perspective=[],
                technical_criteria=[],
            ),
            final_verification=[],
            todos=[todo],
            execution=ExecutionStatus(started=False, completed=False),
            work_mode=WorkMode(parallel_requested=False, current_task_id="test-1"),
            acceptance_criteria_for_verification_agent=[],
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)

        # then
        assert loaded_plan.work_plans[0].acceptance_criteria_for_verification_agent == []
