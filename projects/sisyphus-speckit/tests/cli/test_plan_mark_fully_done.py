from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import anyio
import pytest
from sisyphus_core.core.plans.loader import load_plan, save_plan
from sisyphus_core.core.plans.models import (
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
from typer.testing import CliRunner

from sisyphus_speckit.plan import plan_app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


def test_mark_fully_done__if_valid_evidence__marks_fully_done(tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_path = tasks_dir / "test_plan.yaml"
    status_path = sisyphus_dir / "status.json"

    verification_spec: list[VerificationItem] = [
        VerificationItem(
            id="verify-1",
            title="Test verification",
            description="Test",
            verified=False,
            orchestrator_manually_verified=False,
            manual_verification_evidence="",
            bash=[
                BashVerification(
                    execute="echo 'test'",
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
        status=TodoStatus.pending,
        verification_spec=verification_spec,
        acceptance_criteria=[],
    )

    work_plan = WorkPlan(
        id="test-plan",
        name="Test Plan",
        depends_on=[],
        user_request=UserRequest(original="Test", created_at=datetime.now(UTC).isoformat()),
        objectives=Objectives(core="Test", detailed=[]),
        background=Background(current_situation="Test", reason_for_change="Test", changes_to_make="Test"),
        required_background=RequiredBackground(description="Test", references=[]),
        workflow=Workflow(dependency_diagram="", critical_path=[]),
        success_vision=SuccessVision(user_perspective=[], business_perspective=[], technical_criteria=[]),
        final_verification=[],
        todos=[todo],
        execution=ExecutionStatus(started=False, completed=False, fully_done_at=None),
        work_mode=WorkMode(parallel_requested=False),
        acceptance_criteria_for_verification_agent=[],
    )

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
        work_plans=[work_plan],
    )

    anyio.run(save_plan, plan_path, plan_doc)

    status_data = {
        "current_plan": {
            "plan_path": str(plan_path.relative_to(tmp_path)),
            "plan_root": str(tmp_path),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    }
    _ = status_path.write_text(json.dumps(status_data))

    # when
    result = runner.invoke(
        plan_app,
        [
            "mark fully-done",
            "--evidence",
            "All tasks completed, all tests pass, documentation updated, PR reviewed and merged",
            "--cwd",
            str(tmp_path),
        ],
    )

    # then
    assert result.exit_code == 0
    assert "fully done 마킹 완료" in result.stdout

    reloaded = anyio.run(load_plan, plan_path)
    assert reloaded.work_plans[0].execution.fully_done_at is not None
    assert (
        reloaded.work_plans[0].fully_done_evidence
        == "All tasks completed, all tests pass, documentation updated, PR reviewed and merged"
    )


def test_mark_fully_done__if_no_current_plan__returns_error(tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()

    status_path = sisyphus_dir / "status.json"
    status_data = {"current_plan": None}
    _ = status_path.write_text(json.dumps(status_data))

    # when
    result = runner.invoke(
        plan_app,
        [
            "mark fully-done",
            "--evidence",
            "test evidence",
            "--cwd",
            str(tmp_path),
        ],
    )

    # then
    assert result.exit_code == 1
    assert "활성화된 작업 계획이 없습니다" in result.stdout


def test_mark_fully_done__if_no_work_plans__returns_error(tmp_path: Path) -> None:
    # given
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_path = tasks_dir / "test_plan.yaml"
    status_path = sisyphus_dir / "status.json"

    plan_doc = PlanDocument(
        version="3.0",
        metadata=Metadata(created_at=datetime.now(UTC).isoformat()),
        work_plans=[],
    )

    anyio.run(save_plan, plan_path, plan_doc)

    status_data = {
        "current_plan": {
            "plan_path": str(plan_path.relative_to(tmp_path)),
            "plan_root": str(tmp_path),
            "updated_at": datetime.now(UTC).isoformat(),
        }
    }
    _ = status_path.write_text(json.dumps(status_data))

    # when
    result = runner.invoke(
        plan_app,
        [
            "mark fully-done",
            "--evidence",
            "test evidence",
            "--cwd",
            str(tmp_path),
        ],
    )

    # then
    assert result.exit_code == 1
    assert "작업 계획에 work_plans가 없습니다" in result.stdout
