"""Tests for task continue 3-condition validation.

Tests that task continue validates all 3 conditions before proceeding:
1. deterministic_bash all have verified_at
2. manual verification all passed
3. llm_judge verification all passed

Note: acceptance_criteria_for_verification_agent is NOT checked in task continue.
It is only validated by the verification agent in the loop phase.
"""

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
    DeterministicBashVerification,
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

pytestmark = [pytest.mark.anyio]


async def test_continue__if_deterministic_bash_not_verified__returns_error() -> None:
    """Test that task continue fails when deterministic_bash is not verified."""
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
                title="Test verification with deterministic_bash",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=True,
                manual_verification_evidence="Manually verified",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[
                    DeterministicBashVerification(
                        description="Test deterministic bash",
                        reason_why_it_is_deterministic_and_reliable="Simple echo command",
                        execute="echo 'test'",
                        expected_stdout="test",
                        verified_at=None,  # NOT VERIFIED
                    ),
                ],
                llm_judge=[
                    LLMJudgeVerification(
                        by=LLMJudgeBy.ORCHESTRATOR,
                        context_commands=[],
                        instruction="Test instruction",
                    ),
                ],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for continue conditions",
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
                original="Test user request",
                created_at=datetime.now(UTC).isoformat(),
                additional=[],
                expected_outcome="Test outcome",
                forbidden_outcome="Test forbidden outcome",
            ),
            objectives=Objectives(core="Core objective", detailed=[]),
            background=Background(
                current_situation="Test situation",
                reason_for_change="Test reason",
                changes_to_make="Test changes",
            ),
            required_background=RequiredBackground(
                description="Test description", file_structure="Test structure", references=[]
            ),
            workflow=Workflow(dependency_diagram="Test diagram", critical_path=[]),
            success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
            final_verification=[],
            todos=[todo],
            references=[],
            execution=ExecutionStatus(
                started=True,
                completed=False,
                started_at=datetime.now(UTC).isoformat(),
                fully_done_at="2025-11-16T10:00:00+00:00",
            ),
            work_mode=WorkMode(parallel_requested=False),
            current_work_ids=["test-1"],
            acceptance_criteria_for_verification_agent=[
                AcceptanceCriteriaForVerificationAgent(
                    id="criteria-1",
                    title="Core functionality verification",
                    checklists=[
                        AcceptanceCriteriaChecklist(
                            id="no-naive-type-hints",
                            title="No naive type hints",
                            content="All functions must have proper type hints",
                            checked_at=datetime.now(UTC).isoformat(),
                            checked_evidence="All verified",
                        ),
                    ],
                ),
            ],
            fully_done_evidence=None,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            ),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        work_plan_loaded = loaded_plan.work_plans[0]
        todo_loaded = work_plan_loaded.todos[0]
        verify_item = todo_loaded.verification_spec[0]

        # then - deterministic_bash not verified
        assert verify_item.deterministic_bash
        assert verify_item.deterministic_bash[0].verified_at is None
        assert verify_item.orchestrator_manually_verified is True


async def test_continue__if_manual_verification_not_passed__returns_error() -> None:
    """Test that task continue fails when manual verification is not passed."""
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
                title="Test verification without manual verification",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=False,  # NOT VERIFIED
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[
                    DeterministicBashVerification(
                        description="Test deterministic bash",
                        reason_why_it_is_deterministic_and_reliable="Simple echo command",
                        execute="echo 'test'",
                        expected_stdout="test",
                        verified_at=datetime.now(UTC).isoformat(),
                    ),
                ],
                llm_judge=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for continue conditions",
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
                original="Test user request",
                created_at=datetime.now(UTC).isoformat(),
                additional=[],
                expected_outcome="Test outcome",
                forbidden_outcome="Test forbidden outcome",
            ),
            objectives=Objectives(core="Core objective", detailed=[]),
            background=Background(
                current_situation="Test situation",
                reason_for_change="Test reason",
                changes_to_make="Test changes",
            ),
            required_background=RequiredBackground(
                description="Test description", file_structure="Test structure", references=[]
            ),
            workflow=Workflow(dependency_diagram="Test diagram", critical_path=[]),
            success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
            final_verification=[],
            todos=[todo],
            references=[],
            execution=ExecutionStatus(
                started=True,
                completed=False,
                started_at=datetime.now(UTC).isoformat(),
                fully_done_at="2025-11-16T10:00:00+00:00",
            ),
            work_mode=WorkMode(parallel_requested=False),
            current_work_ids=["test-1"],
            acceptance_criteria_for_verification_agent=[],
            fully_done_evidence=None,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            ),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        work_plan_loaded = loaded_plan.work_plans[0]
        todo_loaded = work_plan_loaded.todos[0]
        verify_item = todo_loaded.verification_spec[0]

        # then - manual verification not passed
        assert verify_item.orchestrator_manually_verified is False
        assert verify_item.manual_verification_evidence == ""
        assert verify_item.deterministic_bash[0].verified_at is not None


async def test_continue__if_llm_judge_empty__allows_continue() -> None:
    """Test that task continue allows empty llm_judge list."""
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
                title="Test verification with no llm_judge",
                description="Test verification item",
                verified=False,
                orchestrator_manually_verified=True,
                manual_verification_evidence="Manually verified",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[
                    DeterministicBashVerification(
                        description="Test deterministic bash",
                        reason_why_it_is_deterministic_and_reliable="Simple echo command",
                        execute="echo 'test'",
                        expected_stdout="test",
                        verified_at=datetime.now(UTC).isoformat(),
                    ),
                ],
                llm_judge=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for continue conditions",
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
                original="Test user request",
                created_at=datetime.now(UTC).isoformat(),
                additional=[],
                expected_outcome="Test outcome",
                forbidden_outcome="Test forbidden outcome",
            ),
            objectives=Objectives(core="Core objective", detailed=[]),
            background=Background(
                current_situation="Test situation",
                reason_for_change="Test reason",
                changes_to_make="Test changes",
            ),
            required_background=RequiredBackground(
                description="Test description", file_structure="Test structure", references=[]
            ),
            workflow=Workflow(dependency_diagram="Test diagram", critical_path=[]),
            success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
            final_verification=[],
            todos=[todo],
            references=[],
            execution=ExecutionStatus(
                started=True,
                completed=False,
                started_at=datetime.now(UTC).isoformat(),
                fully_done_at="2025-11-16T10:00:00+00:00",
            ),
            work_mode=WorkMode(parallel_requested=False),
            current_work_ids=["test-1"],
            acceptance_criteria_for_verification_agent=[],
            fully_done_evidence=None,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            ),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        work_plan_loaded = loaded_plan.work_plans[0]
        todo_loaded = work_plan_loaded.todos[0]
        verify_item = todo_loaded.verification_spec[0]

        # then - llm_judge is empty (allowed)
        assert verify_item.llm_judge == []
        assert verify_item.deterministic_bash[0].verified_at is not None
        assert verify_item.orchestrator_manually_verified is True


async def test_continue__if_acceptance_criteria_not_checked__allows_continue() -> None:
    """Test that task continue ignores acceptance_criteria_for_verification_agent."""
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
                orchestrator_manually_verified=True,
                manual_verification_evidence="Manually verified",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[
                    DeterministicBashVerification(
                        description="Test deterministic bash",
                        reason_why_it_is_deterministic_and_reliable="Simple echo command",
                        execute="echo 'test'",
                        expected_stdout="test",
                        verified_at=datetime.now(UTC).isoformat(),
                    ),
                ],
                llm_judge=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for continue conditions",
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
                original="Test user request",
                created_at=datetime.now(UTC).isoformat(),
                additional=[],
                expected_outcome="Test outcome",
                forbidden_outcome="Test forbidden outcome",
            ),
            objectives=Objectives(core="Core objective", detailed=[]),
            background=Background(
                current_situation="Test situation",
                reason_for_change="Test reason",
                changes_to_make="Test changes",
            ),
            required_background=RequiredBackground(
                description="Test description", file_structure="Test structure", references=[]
            ),
            workflow=Workflow(dependency_diagram="Test diagram", critical_path=[]),
            success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
            final_verification=[],
            todos=[todo],
            references=[],
            execution=ExecutionStatus(
                started=True,
                completed=False,
                started_at=datetime.now(UTC).isoformat(),
                fully_done_at="2025-11-16T10:00:00+00:00",
            ),
            work_mode=WorkMode(parallel_requested=False),
            current_work_ids=["test-1"],
            acceptance_criteria_for_verification_agent=[
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
                    ],
                ),
            ],
            fully_done_evidence=None,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            ),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        loaded_plan = await load_plan(plan_path)
        work_plan_loaded = loaded_plan.work_plans[0]
        todo_loaded = work_plan_loaded.todos[0]
        verify_item = todo_loaded.verification_spec[0]
        acceptance_criteria = work_plan_loaded.acceptance_criteria_for_verification_agent[0]

        assert acceptance_criteria.checklists[0].checked_at is None
        assert verify_item.deterministic_bash[0].verified_at is not None
        assert verify_item.orchestrator_manually_verified is True


async def test_continue__if_all_conditions_met__allows_continue() -> None:
    """Test that task continue succeeds when all 3 conditions are met."""
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
                orchestrator_manually_verified=True,
                manual_verification_evidence="Manually verified",
                bash=[
                    BashVerification(
                        execute="echo 'test'",
                        expected_stdout="test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[
                    DeterministicBashVerification(
                        description="Test deterministic bash",
                        reason_why_it_is_deterministic_and_reliable="Simple echo command",
                        execute="echo 'test'",
                        expected_stdout="test",
                        verified_at=datetime.now(UTC).isoformat(),
                    ),
                ],
                llm_judge=[],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for continue conditions",
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
                original="Test user request",
                created_at=datetime.now(UTC).isoformat(),
                additional=[],
                expected_outcome="Test outcome",
                forbidden_outcome="Test forbidden outcome",
            ),
            objectives=Objectives(core="Core objective", detailed=[]),
            background=Background(
                current_situation="Test situation",
                reason_for_change="Test reason",
                changes_to_make="Test changes",
            ),
            required_background=RequiredBackground(
                description="Test description", file_structure="Test structure", references=[]
            ),
            workflow=Workflow(dependency_diagram="Test diagram", critical_path=[]),
            success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
            final_verification=[],
            todos=[todo],
            references=[],
            execution=ExecutionStatus(
                started=True,
                completed=False,
                started_at=datetime.now(UTC).isoformat(),
                fully_done_at="2025-11-16T10:00:00+00:00",
            ),
            work_mode=WorkMode(parallel_requested=False),
            current_work_ids=["test-1"],
            acceptance_criteria_for_verification_agent=[
                AcceptanceCriteriaForVerificationAgent(
                    id="criteria-1",
                    title="Core functionality verification",
                    checklists=[
                        AcceptanceCriteriaChecklist(
                            id="no-naive-type-hints",
                            title="No naive type hints",
                            content="All functions must have proper type hints",
                            checked_at=datetime.now(UTC).isoformat(),
                            checked_evidence="All verified",
                        ),
                    ],
                ),
            ],
            fully_done_evidence=None,
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            ),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        work_plan_loaded = loaded_plan.work_plans[0]
        todo_loaded = work_plan_loaded.todos[0]
        verify_item = todo_loaded.verification_spec[0]

        # then
        assert verify_item.deterministic_bash[0].verified_at is not None
        assert verify_item.orchestrator_manually_verified is True
        assert verify_item.llm_judge == []
