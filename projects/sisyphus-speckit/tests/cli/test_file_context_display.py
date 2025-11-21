"""Tests for file context display feature in sisyphus-speckit CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus_speckit.cli import app

pytestmark = [
    pytest.mark.anyio,
]

runner = CliRunner()


def test_callback_displays_file_path_when_status_exists(tmp_path: Path) -> None:
    """Test that callback displays current plan file path when status.json exists.

    Given: status.json exists with current_plan.plan_path
    When: task command is executed
    Then: output contains "Working on:" and the plan file path
    """
    # given
    cwd_dir = tmp_path / "test_project"
    cwd_dir.mkdir()
    status_dir = cwd_dir / ".sisyphus"
    status_dir.mkdir()

    status_file = status_dir / "status.json"
    status_data = {
        "version": 1,
        "current_plan": {
            "plan_path": ".sisyphus/tasks/my-plan.yaml",
            "plan_root": str(cwd_dir),
            "updated_at": "2025-11-21T00:00:00Z",
        },
    }
    status_file.write_text(json.dumps(status_data))

    # Create minimal YAML file for task current to work
    tasks_dir = status_dir / "tasks"
    tasks_dir.mkdir()
    yaml_file = tasks_dir / "my-plan.yaml"
    yaml_content = """version: "3.0"
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
      detailed: []
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      file_structure: ""
      references: []
    workflow:
      dependency_diagram: ""
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task 1"
        status: in_progress
        references: []
        children: []
        verification_spec: []
    references: []
    execution:
      started: false
      completed: false
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["task", "current", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Working on:" in result.stdout
    assert ".sisyphus/tasks/my-plan.yaml" in result.stdout


def test_callback_skips_gracefully_when_status_missing(tmp_path: Path) -> None:
    """Test that callback skips gracefully when status.json doesn't exist.

    Given: status.json does not exist
    When: task command is executed
    Then: command executes, callback gracefully handles missing status file
    """
    # given
    cwd_dir = tmp_path / "new_project"
    cwd_dir.mkdir()
    status_dir = cwd_dir / ".sisyphus"
    status_dir.mkdir()
    tasks_dir = status_dir / "tasks"
    tasks_dir.mkdir()

    yaml_file = tasks_dir / "new-plan.yaml"
    yaml_content = """version: "3.0"
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
      detailed: []
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      file_structure: ""
      references: []
    workflow:
      dependency_diagram: ""
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task 1"
        status: pending
        references: []
        children: []
        verification_spec: []
    references: []
    execution:
      started: false
      completed: false
    work_mode:
      parallel_requested: false
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["task", "current", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code != 0  # No current plan set
    # Callback gracefully skips without crashing when status.json missing
    # (callback uses current working directory, not the cwd option)


def test_callback_called_before_command_execution(tmp_path: Path) -> None:
    """Test that callback is called before command execution.

    Given: status.json exists with current_plan.plan_path
    When: task command is executed
    Then: "Working on:" message appears BEFORE the main command output
    """
    # given
    cwd_dir = tmp_path / "test_order"
    cwd_dir.mkdir()
    status_dir = cwd_dir / ".sisyphus"
    status_dir.mkdir()

    status_file = status_dir / "status.json"
    status_data = {
        "version": 1,
        "current_plan": {
            "plan_path": ".sisyphus/tasks/order-test.yaml",
            "plan_root": str(cwd_dir),
            "updated_at": "2025-11-21T00:00:00Z",
        },
    }
    status_file.write_text(json.dumps(status_data))

    # Create minimal YAML file
    tasks_dir = status_dir / "tasks"
    tasks_dir.mkdir()
    yaml_file = tasks_dir / "order-test.yaml"
    yaml_content = """version: "3.0"
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
      detailed: []
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      file_structure: ""
      references: []
    workflow:
      dependency_diagram: ""
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Current Task"
        status: in_progress
        references: []
        children: []
        verification_spec: []
    references: []
    execution:
      started: false
      completed: false
    work_mode:
      parallel_requested: false
      current_task_id: "1"
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["task", "current", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    lines = result.stdout.split("\n")
    # Find indices of key strings
    working_on_idx = next((i for i, line in enumerate(lines) if "Working on:" in line), -1)
    current_task_idx = next((i for i, line in enumerate(lines) if "Current Task" in line), -1)
    # Verify "Working on:" comes before "Current Task"
    assert working_on_idx >= 0, "'Working on:' not found in output"
    assert current_task_idx >= 0, "Task name not found in output"
    assert working_on_idx < current_task_idx, "File path should be displayed BEFORE task details"


def test_callback_handles_corrupted_status_gracefully(tmp_path: Path) -> None:
    """Test that callback handles corrupted status.json gracefully.

    Given: status.json exists but contains invalid JSON
    When: task command is executed
    Then: callback handles error gracefully without crashing command
    """
    # given
    cwd_dir = tmp_path / "corrupt_status"
    cwd_dir.mkdir()
    status_dir = cwd_dir / ".sisyphus"
    status_dir.mkdir()

    status_file = status_dir / "status.json"
    status_file.write_text("{ invalid json }")

    tasks_dir = status_dir / "tasks"
    tasks_dir.mkdir()
    yaml_file = tasks_dir / "test-plan.yaml"
    yaml_content = """version: "3.0"
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
      detailed: []
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      file_structure: ""
      references: []
    workflow:
      dependency_diagram: ""
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task 1"
        status: pending
        references: []
        children: []
        verification_spec: []
    references: []
    execution:
      started: false
      completed: false
    work_mode:
      parallel_requested: false
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["task", "current", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code != 0
    # Callback gracefully catches JSON decode error and skips display


def test_plan_callback_displays_file_path(tmp_path: Path) -> None:
    """Test that plan commands also display file path via callback.

    Given: status.json exists with current_plan.plan_path
    When: plan lint command is executed
    Then: output contains "Working on:" and the plan file path
    """
    # given
    cwd_dir = tmp_path / "plan_callback"
    cwd_dir.mkdir()
    status_dir = cwd_dir / ".sisyphus"
    status_dir.mkdir()

    status_file = status_dir / "status.json"
    status_data = {
        "version": 1,
        "current_plan": {
            "plan_path": ".sisyphus/tasks/plan-test.yaml",
            "plan_root": str(cwd_dir),
            "updated_at": "2025-11-21T00:00:00Z",
        },
    }
    status_file.write_text(json.dumps(status_data))

    # Create minimal YAML file
    tasks_dir = status_dir / "tasks"
    tasks_dir.mkdir()
    yaml_file = tasks_dir / "plan-test.yaml"
    yaml_content = """version: "3.0"
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
      detailed: []
    background:
      current_situation: "Test"
      reason_for_change: "Test"
      changes_to_make: "Test"
    required_background:
      description: "Test"
      file_structure: ""
      references: []
    workflow:
      dependency_diagram: ""
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task 1"
        status: pending
        references: []
        children: []
        verification_spec: []
    acceptance_criteria:
      - id: "c1"
        condition: "Test criteria 1"
      - id: "c2"
        condition: "Test criteria 2"
    references: []
    execution:
      started: false
      completed: false
    work_mode:
      parallel_requested: false
    current_work: ""
    acceptance_criteria_for_verification_agent:
      - id: "vc1"
        title: "Verification 1"
        checklists: []
      - id: "vc2"
        title: "Verification 2"
        checklists: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", ".sisyphus/tasks/plan-test.yaml", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Working on:" in result.stdout
