"""Tests for manual_mark bash verification prerequisite and executor agent blocking."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sisyphus_speckit.task import task_app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


def test_manual_mark__if_bash_not_verified__returns_error(tmp_path: Path) -> None:
    """
    Given: A task with unverified bash items
    When: Attempting manual mark
    Then: Returns error with 3-step guidance
    """
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
            deterministic_bash:
              - description: "Test bash verification"
                reason_why_it_is_deterministic_and_reliable: "Echo command always produces same output"
                execute: "echo test"
                expected_exit_code: 0
                verified_at: null
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
    _ = yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    _ = status_file.write_text(status_content)

    evidence = "a" * 100

    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    assert result.exit_code == 1
    assert "Bash verification이 통과되지 않았습니다" in result.output
    assert "1단계" in result.output
    assert "2단계" in result.output
    assert "3단계" in result.output
    assert "sisyphus-speckit task verify bash" in result.output


def test_manual_mark__if_bash_verified__allows_marking(tmp_path: Path) -> None:
    """
    Given: A task with all bash items verified
    When: Attempting manual mark
    Then: Succeeds and marks as verified
    """
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
            deterministic_bash:
              - description: "Test bash verification"
                reason_why_it_is_deterministic_and_reliable: "Echo command always produces same output"
                execute: "echo test"
                expected_exit_code: 0
                verified_at: "2025-01-01T00:00:00Z"
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
    _ = yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    _ = status_file.write_text(status_content)

    evidence = "a" * 100

    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    assert result.exit_code == 0
    assert "수동 검증이 완료 표시되었습니다" in result.output


def test_manual_mark__if_no_bash_items__allows_marking(tmp_path: Path) -> None:
    """
    Given: A task with no bash verification items
    When: Attempting manual mark
    Then: Succeeds without bash prerequisite check
    """
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
            llm_judge:
              - instruction: "Test LLM judge instruction"
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
    _ = yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    _ = status_file.write_text(status_content)

    evidence = "a" * 100

    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    assert result.exit_code == 0
    assert "수동 검증이 완료 표시되었습니다" in result.output


def test_manual_mark__if_executor_agent__returns_illegal_error(tmp_path: Path) -> None:
    """
    Given: Executor agent tries to run manual-mark
    When: Environment variable ANTHROPIC_CLI_AGENT_NAME contains 'executor'
    Then: Returns ILLEGAL error in English
    """
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
            llm_judge:
              - instruction: "Test LLM judge instruction"
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
    _ = yaml_file.write_text(yaml_content)

    status_file = tmp_path / ".sisyphus" / "status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_content = (
        '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", '
        '"plan_id": "test-plan", "plan_root": ".sisyphus/tasks", "updated_at": "2025-01-01T00:00:00Z"}}'
    )
    _ = status_file.write_text(status_content)

    evidence = "a" * 100

    with patch.dict(os.environ, {"ANTHROPIC_CLI_AGENT_NAME": "sisyphus-executor"}):
        result = runner.invoke(
            task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)]
        )

    assert result.exit_code == 1
    assert "ILLEGAL" in result.output
    assert "Executor agents cannot run verification commands" in result.output
    assert "orchestrator" in result.output
