from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus_core.cli.task import task_app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


def test_verify_manual_mark__if_evidence_exactly_100_chars__succeeds(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / ".sisyphus" / "tasks" / "test-plan.yaml"
    yaml_file.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """version: '3.0'
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
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
    workflow:
      dependency_diagram: ""
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Test Task"
        description: "Test"
        status: in_progress
        references: []
        verification_spec:
          - id: "v1"
            title: "Manual Verification"
            description: "Test"
            category: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
                expected_stdout: "test"
                expected_exit_code: 0
            llm_judge: []
    references: []
    execution:
      started: true
      completed: false
      started_at: "2025-01-01T00:00:00Z"
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    evidence = "a" * 100  # exactly 100 characters

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0


def test_verify_manual_mark__if_evidence_99_chars__raises_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / ".sisyphus" / "tasks" / "test-plan.yaml"
    yaml_file.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """version: '3.0'
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
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
    workflow:
      dependency_diagram: ""
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Test Task"
        description: "Test"
        status: in_progress
        references: []
        verification_spec:
          - id: "v1"
            title: "Manual Verification"
            description: "Test"
            category: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
                expected_stdout: "test"
                expected_exit_code: 0
            llm_judge: []
    references: []
    execution:
      started: true
      completed: false
      started_at: "2025-01-01T00:00:00Z"
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    evidence = "a" * 99  # 99 characters

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code != 0
    assert "100" in result.output
    assert "증거" in result.output


def test_verify_manual_mark__if_evidence_200_chars__succeeds(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / ".sisyphus" / "tasks" / "test-plan.yaml"
    yaml_file.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """version: '3.0'
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
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
    workflow:
      dependency_diagram: ""
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Test Task"
        description: "Test"
        status: in_progress
        references: []
        verification_spec:
          - id: "v1"
            title: "Manual Verification"
            description: "Test"
            category: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
                expected_stdout: "test"
                expected_exit_code: 0
            llm_judge: []
    references: []
    execution:
      started: true
      completed: false
      started_at: "2025-01-01T00:00:00Z"
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    evidence = "a" * 200  # 200 characters

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0


def test_verify_manual_mark__if_empty_evidence__raises_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / ".sisyphus" / "tasks" / "test-plan.yaml"
    yaml_file.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """version: '3.0'
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
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
    workflow:
      dependency_diagram: ""
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Test Task"
        description: "Test"
        status: in_progress
        references: []
        verification_spec:
          - id: "v1"
            title: "Manual Verification"
            description: "Test"
            category: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
                expected_stdout: "test"
                expected_exit_code: 0
            llm_judge: []
    references: []
    execution:
      started: true
      completed: false
      started_at: "2025-01-01T00:00:00Z"
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    evidence = ""  # empty string

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code != 0
    assert "100" in result.output


def test_verify_manual_mark__error_message_contains_required_parts(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / ".sisyphus" / "tasks" / "test-plan.yaml"
    yaml_file.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """version: '3.0'
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
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
    workflow:
      dependency_diagram: ""
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Test Task"
        description: "Test"
        status: in_progress
        references: []
        verification_spec:
          - id: "v1"
            title: "Manual Verification"
            description: "Test"
            category: "Test"
            verified: false
            orchestrator_manually_verified: false
            manual_verification_evidence: ""
            bash:
              - execute: "echo test"
                expected_stdout: "test"
                expected_exit_code: 0
            llm_judge: []
    references: []
    execution:
      started: true
      completed: false
      started_at: "2025-01-01T00:00:00Z"
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    status_file.write_text(status_content)

    evidence = "short"  # too short

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code != 0
    # Check error message contains reason
    assert "이유" in result.output or "철저한" in result.output
    # Check error message contains example
    assert "예시" in result.output or "Chrome" in result.output
    # Check error message contains guidance
    assert "가이드" in result.output or "검증" in result.output
