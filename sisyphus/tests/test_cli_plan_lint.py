"""CLI plan lint command integration tests."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.cli import app

pytestmark = [pytest.mark.anyio]
runner = CliRunner()


async def test_plan_lint__when_valid_yaml__exits_0(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
user_request:
  original: "Test"
  timestamp: "2025-01-01"
objectives:
  core: "Test objective"
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Test"
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
  progress:
    total_tasks: 0
    completed: 0
    in_progress: 0
    pending: 0
  current_work: "None"
workflow:
  dependency_diagram: "Test"
todos: []
success_vision: {}
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 0
    assert "YAML validation passed" in result.stdout


async def test_plan_lint__when_missing_fields__exits_1_and_shows_errors(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "invalid.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Validation failed" in result.stdout
    assert "error" in result.stdout.lower()


async def test_plan_lint__when_type_mismatch__exits_1_and_shows_type_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "type_error.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
user_request:
  original: "Test"
  timestamp: "2025-01-01"
objectives:
  core: "Test"
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Test"
status:
  execution:
    started: "true"
    completed: false
  work_mode:
    parallel_requested: false
  progress:
    total_tasks: 0
    completed: 0
    in_progress: 0
    pending: 0
  current_work: "None"
workflow:
  dependency_diagram: "Test"
todos: []
success_vision: {}
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Validation failed" in result.stdout
    assert "status.execution.started" in result.stdout
    assert "Type mismatch" in result.stdout


async def test_plan_lint__when_file_not_found__exits_1() -> None:
    # when
    result = runner.invoke(app, ["plan", "lint", "--file", "nonexistent.yaml"])

    # then
    assert result.exit_code == 1
    assert "File not found" in result.stdout


async def test_plan_lint__when_invalid_enum__exits_1_and_shows_enum_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "enum_error.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
  updated_at: "2025-01-01"
user_request:
  original: "Test"
  timestamp: "2025-01-01"
objectives:
  core: "Test"
background:
  current_situation: "A"
  reason_for_change: "B"
  changes_to_make: "C"
required_background:
  description: "Test"
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
  progress:
    total_tasks: 0
    completed: 0
    in_progress: 0
    pending: 0
  current_work: "None"
workflow:
  dependency_diagram: "Test"
todos:
  - id: "1"
    title: "Task"
    status: "invalid_status"
    created_at: "2025-01-01"
    updated_at: "2025-01-01"
success_vision: {}
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Validation failed" in result.stdout
    assert "todos[0].status" in result.stdout
    assert "Invalid enum" in result.stdout


async def test_plan_lint__when_yaml_syntax_error__exits_1_and_shows_parsing_error(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "malformed.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01"
  invalid indentation
    bad_field: "value"
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "parsing error" in result.stdout.lower() or "yaml" in result.stdout.lower()
