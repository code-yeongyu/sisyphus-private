"""CLI plan lint command integration tests."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ..cli import app

pytestmark = [pytest.mark.anyio]
runner = CliRunner()


async def test_plan_lint__when_valid_yaml__exits_0(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
work_plans:
  - id: "test-plan"
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test"
      created_at: "2025-01-01"
      additional: []
    objectives:
      core: "Test objective"
      detailed: []
    background:
      current_situation: "A"
      reason_for_change: "B"
      changes_to_make: "C"
    required_background:
      description: "Test"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Test task"
        status: "pending"
    execution:
      started: false
      completed: false
      started_at: null
      completed_at: null
    work_mode:
      parallel_requested: false
      current_task_id: null
    current_work: ""
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 0
    assert "YAML validation passed" in result.stdout


async def test_plan_lint__when_missing_fields__exits_1_and_shows_errors(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "invalid.yaml"
    yaml_content = """version: "3.0"
work_plans: []
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "error" in result.stdout.lower()


async def test_plan_lint__when_type_mismatch__exits_1_and_shows_type_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "type_error.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
work_plans:
  - id: "test-plan"
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test"
      created_at: "2025-01-01"
      additional: []
    objectives:
      core: "Test"
      detailed: []
    background:
      current_situation: "A"
      reason_for_change: "B"
      changes_to_make: "C"
    required_background:
      description: "Test"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos: []
    execution:
      started: "not-a-boolean"
      completed: false
      started_at: null
      completed_at: null
    work_mode:
      parallel_requested: false
      current_task_id: null
    current_work: ""
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "work_plans.0.execution.started" in result.stdout
    assert "boolean" in result.stdout


async def test_plan_lint__when_file_not_found__exits_1() -> None:
    # when
    result = runner.invoke(app, ["plan", "lint", "--file", "nonexistent.yaml"])

    # then
    assert result.exit_code == 1
    assert "File not found" in result.stdout


async def test_plan_lint__when_invalid_enum__exits_1_and_shows_enum_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "enum_error.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
work_plans:
  - id: "test-plan"
    name: "Test Plan"
    depends_on: []
    user_request:
      original: "Test"
      created_at: "2025-01-01"
      additional: []
    objectives:
      core: "Test"
      detailed: []
    background:
      current_situation: "A"
      reason_for_change: "B"
      changes_to_make: "C"
    required_background:
      description: "Test"
      file_structure: null
      references: []
    workflow:
      dependency_diagram: "Test"
      critical_path: []
    success_vision:
      user_perspective: []
      business_perspective: []
      technical_criteria: []
    final_verification: []
    todos:
      - id: "1"
        title: "Task"
        status: "invalid_status"
    execution:
      started: false
      completed: false
      started_at: null
      completed_at: null
    work_mode:
      parallel_requested: false
      current_task_id: null
    current_work: ""
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout
    assert "work_plans.0.todos.0.status" in result.stdout
    assert "enum" in result.stdout.lower()


async def test_plan_lint__when_yaml_syntax_error__exits_1_and_shows_parsing_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "malformed.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
  invalid indentation
    bad_field: "value"
"""
    _ = yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "parsing error" in result.stdout.lower() or "yaml" in result.stdout.lower()
