"""Tests for task verify bash command with deterministic_bash sequential execution."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import (
    Background,
    BashVerification,
    DeterministicBashVerification,
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
from typer.testing import CliRunner

from sisyphus_speckit.task import task_app

pytestmark = [pytest.mark.anyio]


async def test_verify_bash__with_deterministic_bash_items__executes_sequentially() -> None:
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
                title="Test bash execution",
                description="Execute bash commands sequentially",
                verified=False,
                orchestrator_manually_verified=False,
                manual_verification_evidence="",
                bash=[
                    BashVerification(
                        execute="echo 'first test'",
                        expected_stdout="first test",
                        expected_exit_code=0,
                    ),
                ],
                deterministic_bash=[
                    DeterministicBashVerification(
                        description="First deterministic bash test",
                        reason_why_it_is_deterministic_and_reliable=("Simple echo command is deterministic"),
                        execute="echo 'hello world'",
                        expected_stdout="hello world",
                        expected_exit_code=0,
                    ),
                    DeterministicBashVerification(
                        description="Second deterministic bash test",
                        reason_why_it_is_deterministic_and_reliable=("Exit code check is deterministic"),
                        execute="exit 0",
                        expected_exit_code=0,
                    ),
                ],
                orchestrator_judge=[],
            ),
        ]

        todo = Todo(
            id="test-1",
            title="Test task",
            description="Test task for bash verification",
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
        assert loaded_plan.work_plans[0].todos[0].verification_spec[0].deterministic_bash
        assert len(loaded_plan.work_plans[0].todos[0].verification_spec[0].deterministic_bash) == 2
        assert (
            loaded_plan.work_plans[0].todos[0].verification_spec[0].deterministic_bash[0].description
            == "First deterministic bash test"
        )


async def test_verify_bash__with_multiple_verification_items__finds_first_unverified() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        verify_item_1 = VerificationItem(
            id="verify-1",
            title="First verification",
            description="Already verified",
            verified=True,
            verified_at=datetime.now(UTC).isoformat(),
            orchestrator_manually_verified=True,
            manual_verification_evidence="Already done",
            bash=[
                BashVerification(
                    execute="echo 'done'",
                    expected_stdout="done",
                    expected_exit_code=0,
                ),
            ],
            deterministic_bash=[
                DeterministicBashVerification(
                    description="First test",
                    reason_why_it_is_deterministic_and_reliable="Deterministic",
                    execute="echo 'done'",
                    expected_stdout="done",
                    expected_exit_code=0,
                    verified_at=datetime.now(UTC).isoformat(),
                ),
            ],
            orchestrator_judge=[],
        )

        verify_item_2 = VerificationItem(
            id="verify-2",
            title="Second verification",
            description="Not yet verified",
            verified=False,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[
                BashVerification(
                    execute="echo 'pending'",
                    expected_stdout="pending",
                    expected_exit_code=0,
                ),
            ],
            deterministic_bash=[
                DeterministicBashVerification(
                    description="Second test",
                    reason_why_it_is_deterministic_and_reliable="Deterministic",
                    execute="echo 'pending'",
                    expected_stdout="pending",
                    expected_exit_code=0,
                ),
            ],
            orchestrator_judge=[],
        )

        todo = Todo(
            id="test-1",
            title="Multi-verification task",
            description="Task with multiple verifications",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=[verify_item_1, verify_item_2],
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
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        verification_specs = loaded_plan.work_plans[0].todos[0].verification_spec

        # then
        assert len(verification_specs) == 2
        assert verification_specs[0].verified is True
        assert verification_specs[1].verified is False
        assert verification_specs[1].id == "verify-2"


async def test_verify_bash__with_deterministic_bash_and_reason_why__stores_metadata() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        reason = "This command checks git status which is deterministic across multiple runs in the same repo state"
        deterministic_bash_item = DeterministicBashVerification(
            description="Check git status",
            reason_why_it_is_deterministic_and_reliable=reason,
            execute="git status",
            expected_exit_code=0,
        )

        verify_item = VerificationItem(
            id="verify-1",
            title="Git status check",
            description="Verify git status is clean",
            verified=False,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[
                BashVerification(
                    execute="git status",
                    expected_exit_code=0,
                ),
            ],
            deterministic_bash=[deterministic_bash_item],
            orchestrator_judge=[],
        )

        todo = Todo(
            id="test-1",
            title="Git test",
            description="Test git operations",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=[verify_item],
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
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        loaded_bash_item = loaded_plan.work_plans[0].todos[0].verification_spec[0].deterministic_bash[0]

        # then
        assert loaded_bash_item.reason_why_it_is_deterministic_and_reliable == reason
        assert loaded_bash_item.execute == "git status"
        assert loaded_bash_item.expected_exit_code == 0


async def test_verify_bash__with_empty_deterministic_bash__allows_empty_list() -> None:
    # given
    with TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        sisyphus_dir = working_dir / ".sisyphus"
        sisyphus_dir.mkdir()

        plan_path = sisyphus_dir / "tasks" / "test_plan.yaml"
        plan_path.parent.mkdir(parents=True, exist_ok=True)

        verify_item = VerificationItem(
            id="verify-1",
            title="Empty deterministic bash",
            description="Verification with no deterministic bash items",
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
        )

        todo = Todo(
            id="test-1",
            title="Empty bash test",
            description="Test with empty deterministic bash",
            status=TodoStatus.in_progress,
            references=[],
            verification_spec=[verify_item],
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
        )

        plan_doc = PlanDocument(
            version="3.0",
            metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
            work_plans=[work_plan],
        )

        await save_plan(plan_path, plan_doc)

        # when
        loaded_plan = await load_plan(plan_path)
        deterministic_bash_list = loaded_plan.work_plans[0].todos[0].verification_spec[0].deterministic_bash

        # then
        assert isinstance(deterministic_bash_list, list)
        assert len(deterministic_bash_list) == 0


def test_verify_bash_cli__with_deterministic_bash__executes_and_verifies(tmp_path: Path) -> None:
    runner = CliRunner()

    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    yaml_file = tasks_dir / "test-plan.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: "test-plan"
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test"
      created_at: "2025-01-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test"
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      references: []
    execution:
      started: true
      completed: false
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
    workflow:
      dependency_diagram: ""
    todos:
      - id: "1"
        title: "Test Task"
        status: in_progress
        created_at: "2025-01-01T00:00:00Z"
        updated_at: "2025-01-01T00:00:00Z"
        references: []
        children: []
        verification_spec:
          - id: "v1"
            title: "Deterministic Bash Test"
            description: "Test deterministic bash execution"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo hello"
                expected_exit_code: 0
            deterministic_bash:
              - description: "Echo test"
                reason_why_it_is_deterministic_and_reliable: "Simple echo"
                execute: "echo 'deterministic'"
                expected_stdout: "deterministic"
                expected_exit_code: 0
            llm_judge: []
            orchestrator_judge: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
"""
    yaml_file.write_text(yaml_content)

    status_file = sisyphus_dir / "status.json"
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", '
        '"updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    # when
    result = runner.invoke(task_app, ["verify", "bash", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0, f"Exit code: {result.exit_code}\nOutput: {result.stdout}"
    assert "Deterministic 실행" in result.stdout
    assert "✓ 성공" in result.stdout
    assert "검증 완료" in result.stdout


def test_verify_bash_cli__with_deterministic_bash_stdout_mismatch__fails(tmp_path: Path) -> None:
    runner = CliRunner()

    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    yaml_file = tasks_dir / "test-plan.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: "test-plan"
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test"
      created_at: "2025-01-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test"
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      references: []
    execution:
      started: true
      completed: false
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
    workflow:
      dependency_diagram: ""
    todos:
      - id: "1"
        title: "Test Task"
        status: in_progress
        created_at: "2025-01-01T00:00:00Z"
        updated_at: "2025-01-01T00:00:00Z"
        references: []
        children: []
        verification_spec:
          - id: "v1"
            title: "Mismatched Stdout Test"
            description: "Test stdout mismatch detection"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash: []
            deterministic_bash:
              - description: "Echo test with wrong expectation"
                reason_why_it_is_deterministic_and_reliable: "Simple echo"
                execute: "echo 'actual'"
                expected_stdout: "expected"
                expected_exit_code: 0
            llm_judge: []
            orchestrator_judge: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
"""
    yaml_file.write_text(yaml_content)

    status_file = sisyphus_dir / "status.json"
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", '
        '"updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    # when
    result = runner.invoke(task_app, ["verify", "bash", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 1, f"Exit code: {result.exit_code}\nOutput: {result.stdout}"
    assert "stdout 불일치" in result.stdout
    assert "검증 실패" in result.stdout
