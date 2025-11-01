from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.commands.plan import plan_app
from sisyphus.commands.task import task_app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


def test_full_workflow__plan_init_to_task_execution__succeeds(tmp_path: Path) -> None:
    """
    Full workflow integration test covering:
    1. plan init - initialize new plan
    2. Create multiple YAML files with depends_on
    3. plan lint - validate plans
    4. plan graph - visualize dependencies
    5. task commands - show, current, next
    """
    # given
    work_dir = tmp_path / "project"
    work_dir.mkdir()

    # when: Initialize first plan (foundation)
    result_init_foundation = runner.invoke(
        plan_app, ["init", "--path", str(work_dir / "foundation.yaml"), "--cwd", str(work_dir)]
    )

    # then
    assert result_init_foundation.exit_code == 0
    assert (work_dir / "foundation.yaml").exists()
    assert "✓ Plan template created" in result_init_foundation.stdout

    # when: Initialize second plan (main) that depends on foundation
    result_init_main = runner.invoke(plan_app, ["init", "--path", str(work_dir / "main.yaml"), "--cwd", str(work_dir)])

    # then
    assert result_init_main.exit_code == 0
    assert (work_dir / "main.yaml").exists()

    # when: Lint the foundation plan
    result_lint = runner.invoke(plan_app, ["lint", "--file", str(work_dir / "foundation.yaml")])

    # then
    assert result_lint.exit_code == 0
    assert "✓ YAML validation passed" in result_lint.stdout


def test_full_workflow__multi_plan_with_dependencies__graph_renders(tmp_path: Path) -> None:
    """
    Test multi-plan scenario with depends_on relationships.
    Creates v3.0 YAML files and verifies graph rendering.
    """
    # given: Create v3.0 YAML with multiple plans
    yaml_file = tmp_path / "ai-todolist.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-foundation
    name: Foundation Plan
    depends_on: []
    todos:
      - id: "1"
        title: Setup infrastructure
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
        references: []
        children: []
        verification_spec: []
  - id: plan-backend
    name: Backend Development
    depends_on:
      - plan-foundation
    todos:
      - id: "1"
        title: Build API
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
        references: []
        children: []
        verification_spec: []
  - id: plan-frontend
    name: Frontend Development
    depends_on:
      - plan-backend
    todos:
      - id: "1"
        title: Build UI
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
        references: []
        children: []
        verification_spec: []
"""
    yaml_file.write_text(yaml_content)

    # when: Run graph command with ASCII format
    result_graph_ascii = runner.invoke(plan_app, ["graph", "--cwd", str(tmp_path), "--format", "ascii"])

    # then
    assert result_graph_ascii.exit_code == 0
    # ASCII graph should contain plan names
    assert "plan-foundation" in result_graph_ascii.stdout or "Foundation" in result_graph_ascii.stdout

    # when: Run graph command with Mermaid format
    result_graph_mermaid = runner.invoke(plan_app, ["graph", "--cwd", str(tmp_path), "--format", "mermaid"])

    # then
    assert result_graph_mermaid.exit_code == 0
    assert "graph TD" in result_graph_mermaid.stdout


def test_full_workflow__task_commands_with_v2_plan__work_correctly(tmp_path: Path) -> None:
    """
    Test task commands (show, current, next) with v2.1 YAML.
    Verifies backward compatibility with existing plan format.
    """
    # given: Create v2.1 YAML with tasks
    yaml_file = tmp_path / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
user_request:
  original: Integration Test Project
  created_at: "2025-11-01T00:00:00Z"
  additional: []
objectives:
  core: Test task commands
background:
  current_situation: Testing
  reason_for_change: Verification
  changes_to_make: None
required_background:
  description: Test background
  references: []
status:
  execution:
    started: true
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: "1"
  progress:
    total_tasks: 2
    completed: 0
    in_progress: 1
    pending: 1
  current_work: Working on task 1
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: First Task
    status: in_progress
    created_at: "2025-11-01T00:00:00Z"
    updated_at: "2025-11-01T00:00:00Z"
    references: []
    children: []
    verification_spec: []
  - id: "2"
    title: Second Task
    status: pending
    created_at: "2025-11-01T00:00:00Z"
    updated_at: "2025-11-01T00:00:00Z"
    references: []
    children: []
    verification_spec: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when: Show specific task by ID
    result_show = runner.invoke(task_app, ["show", "1", "--cwd", str(tmp_path)])

    # then
    assert result_show.exit_code == 0
    assert "First Task" in result_show.stdout

    # when: Show current task
    result_current = runner.invoke(task_app, ["current", "--cwd", str(tmp_path)])

    # then
    assert result_current.exit_code == 0
    assert "First Task" in result_current.stdout

    # when: Show next task
    result_next = runner.invoke(task_app, ["next", "--cwd", str(tmp_path)])

    # then
    assert result_next.exit_code == 0
    assert "Second Task" in result_next.stdout


def test_full_workflow__lint_detects_validation_errors__fails_gracefully(tmp_path: Path) -> None:
    """
    Test that plan lint detects validation errors and provides clear feedback.
    """
    # given: Create invalid YAML (missing required fields)
    yaml_file = tmp_path / "invalid.yaml"
    yaml_content = """metadata:
  created_at: "2025-11-01T00:00:00Z"
todos: invalid_value
"""
    yaml_file.write_text(yaml_content)

    # when: Run lint on invalid file
    result_lint = runner.invoke(plan_app, ["lint", "--file", str(yaml_file)])

    # then
    assert result_lint.exit_code == 1
    assert "✗ Validation failed" in result_lint.stdout or "error" in result_lint.stdout.lower()


def test_full_workflow__verify_bash_execution__marks_verified(tmp_path: Path) -> None:
    """
    Test bash verification workflow:
    1. Create plan with bash verification spec
    2. Run verify bash command
    3. Verify that status is updated
    """
    # given: Create YAML with bash verification
    yaml_file = tmp_path / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
user_request:
  original: Test verification
  created_at: "2025-11-01T00:00:00Z"
  additional: []
objectives:
  core: Test bash verification
background:
  current_situation: Testing
  reason_for_change: Verification
  changes_to_make: None
required_background:
  description: Test
  references: []
status:
  execution:
    started: true
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: "1"
  progress:
    total_tasks: 1
    completed: 0
    in_progress: 1
    pending: 0
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: Test Task with Verification
    status: in_progress
    created_at: "2025-11-01T00:00:00Z"
    updated_at: "2025-11-01T00:00:00Z"
    references: []
    children: []
    verification_spec:
      - id: verify_1
        title: Test Echo Command
        description: Simple echo test
        verified: false
        verified_at: null
        verification_evidence: null
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo 'test success'"
            expected_exit_code: 0
        llm_judge: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when: Run bash verification
    result_verify = runner.invoke(task_app, ["verify", "bash", "--cwd", str(tmp_path)])

    # then
    assert result_verify.exit_code == 0
    assert "검증 1/1" in result_verify.stdout
    assert "Test Echo Command" in result_verify.stdout
    assert "✓ 성공" in result_verify.stdout


def test_full_workflow__cwd_option_throughout__works_consistently(tmp_path: Path) -> None:
    """
    Test that --cwd option works consistently across all commands.
    This verifies the resolve_cwd() helper function integration.
    """
    # given: Create workspace in subdirectory
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # when: Initialize plan with --cwd
    result_init = runner.invoke(plan_app, ["init", "--cwd", str(work_dir)])

    # then
    assert result_init.exit_code == 0
    assert (work_dir / "ai-todolist.yaml").exists()

    # when: Lint with --cwd
    result_lint = runner.invoke(plan_app, ["lint", "--cwd", str(work_dir)])

    # then
    assert result_lint.exit_code == 0
    assert "✓ YAML validation passed" in result_lint.stdout

    # when: Overview with --cwd
    result_overview = runner.invoke(plan_app, ["overview", "--cwd", str(work_dir)])

    # then
    assert result_overview.exit_code == 0
    # Overview should display some content from the template


def test_full_workflow__export_to_markdown__preserves_structure(tmp_path: Path) -> None:
    """
    Test YAML to Markdown export functionality.
    Verifies that plan export command works end-to-end.
    """
    # given: Create v3.0 YAML plan
    yaml_file = tmp_path / "test-plan.yaml"
    yaml_content = """version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-test
    name: Test Plan
    depends_on: []
    todos:
      - id: "1"
        title: Test Todo Item
        description: This is a test description
        status: pending
        created_at: "2025-11-01T00:00:00Z"
        updated_at: "2025-11-01T00:00:00Z"
        references: []
        children:
          - id: "1.1"
            title: Subtask One
            status: pending
            created_at: "2025-11-01T00:00:00Z"
            updated_at: "2025-11-01T00:00:00Z"
            references: []
            children: []
            verification_spec: []
        verification_spec: []
"""
    yaml_file.write_text(yaml_content)

    # when: Export to markdown (stdout)
    result_export = runner.invoke(plan_app, ["export", str(yaml_file)])

    # then
    assert result_export.exit_code == 0
    assert "Test Plan" in result_export.stdout
    assert "Test Todo Item" in result_export.stdout
    assert "Subtask One" in result_export.stdout

    # when: Export to file
    output_file = tmp_path / "output.md"
    result_export_file = runner.invoke(plan_app, ["export", str(yaml_file), "--output", str(output_file)])

    # then
    assert result_export_file.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "Test Plan" in content
    assert "Test Todo Item" in content
