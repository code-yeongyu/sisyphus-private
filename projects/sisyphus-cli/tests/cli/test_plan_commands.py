from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.cli.plan import plan_app

pytestmark = [
    pytest.mark.anyio,
]

runner = CliRunner()


def test_lint__with_valid_yaml__passes(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "test.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: test-plan
    name: Test Plan
    depends_on: []
    user_request:
      original: "Test request"
      created_at: "2025-01-01T00:00:00Z"
      additional: []
    objectives:
      core: "Test objective"
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
    todos: []
    references: []
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
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(plan_app, ["lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 0
    assert "✓ YAML validation passed" in result.stdout


def test_lint__with_invalid_yaml__fails(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("metadata:\n  invalid: true")

    # when
    result = runner.invoke(plan_app, ["lint", "--file", str(yaml_file)])

    # then
    assert result.exit_code == 1
    assert "Schema validation failed" in result.stdout


def test_lint__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
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
    todos: []
    references: []
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
    current_work: ""
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(plan_app, ["lint", "--file", "ai-todolist.yaml", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0


def test_init__creates_template_file(tmp_path: Path) -> None:
    # given
    output_file = tmp_path / "new-plan.yaml"

    # when
    result = runner.invoke(plan_app, ["init", "--path", str(output_file)])

    # then
    assert result.exit_code == 0
    assert output_file.exists()
    assert "✓ Plan template created" in result.stdout
    content = output_file.read_text()
    assert "metadata:" in content
    assert "user_request:" in content
    assert "todos:" in content


def test_init__with_existing_file__fails(tmp_path: Path) -> None:
    # given
    output_file = tmp_path / "existing.yaml"
    output_file.write_text("existing content")

    # when
    result = runner.invoke(plan_app, ["init", "--path", str(output_file)])

    # then
    assert result.exit_code == 1
    assert "already exists" in result.stdout


def test_init__with_cwd_option__creates_in_cwd(tmp_path: Path) -> None:
    # given
    work_dir = tmp_path / "workdir"
    work_dir.mkdir()

    # when
    result = runner.invoke(plan_app, ["init", "--cwd", str(work_dir)])

    # then
    assert result.exit_code == 0
    assert (work_dir / ".sisyphus" / "tasks" / "ai-todolist.yaml").exists()


def test_graph__with_v3_plan__displays_graph(tmp_path: Path) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)
    plan_file = tasks_dir / "ai-todolist.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: plan1
    name: Plan 1
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
    todos: []
    references: []
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
    current_work: ""
  - id: plan2
    name: Plan 2
    depends_on:
      - plan1
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
    todos: []
    references: []
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
    current_work: ""
"""
    plan_file.write_text(yaml_content)

    # when
    result = runner.invoke(plan_app, ["graph", "--cwd", str(tmp_path), "--format", "ascii"])

    # then
    assert result.exit_code == 0


def test_graph__with_non_v3_plan__shows_warning(tmp_path: Path) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)
    plan_file = tasks_dir / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
"""
    plan_file.write_text(yaml_content)

    # when
    result = runner.invoke(plan_app, ["graph", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 1
    assert "v3.0" in result.stdout or "depends_on" in result.stdout


def test_graph__with_mermaid_format__outputs_mermaid(tmp_path: Path) -> None:
    # given
    tasks_dir = tmp_path / ".sisyphus" / "tasks"
    tasks_dir.mkdir(parents=True)
    plan_file = tasks_dir / "ai-todolist.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
work_plans:
  - id: plan1
    name: Plan 1
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
    todos: []
    references: []
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
    current_work: ""
"""
    plan_file.write_text(yaml_content)

    # when
    result = runner.invoke(plan_app, ["graph", "--cwd", str(tmp_path), "--format", "mermaid"])

    # then
    assert result.exit_code == 0
    assert "graph TD" in result.stdout
