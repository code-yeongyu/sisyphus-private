from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.cli import app

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skip(reason="CLI tests require v2.1 compatibility layer - deferred to post-v3.0 release"),
]

runner = CliRunner()


def test_plan_lint__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "test.yaml"
    yaml_file.write_text("""metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
user_request:
  original: "Test"
  created_at: "2025-11-01T00:00:00Z"
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
""")

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", "test.yaml", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0


def test_plan_overview__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "ai-todolist.yaml"
    yaml_file.write_text("""metadata:
  created_at: "2025-11-01T00:00:00Z"
  updated_at: "2025-11-01T00:00:00Z"
user_request:
  original: "Test"
  created_at: "2025-11-01T00:00:00Z"
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
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: "1"
  progress:
    total_tasks: 1
    completed: 0
    in_progress: 0
    pending: 1
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Task 1"
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
""")

    # when
    result = runner.invoke(app, ["plan", "overview", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Task 1" in result.stdout


def test_plan_init__with_cwd_option__creates_in_cwd(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()

    # when
    result = runner.invoke(app, ["plan", "init", "--path", "new-plan.yaml", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert (cwd_dir / "new-plan.yaml").exists()


def test_plan_graph__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "ai-todolist.yaml"
    yaml_file.write_text("""
version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-test
    name: "Test Plan"
    depends_on: []
    todos: []
    references: []
""")

    # when
    result = runner.invoke(app, ["plan", "graph", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0


def test_plan_export__with_cwd_option__resolves_paths(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "test.yaml"
    yaml_file.write_text("""
version: "3.0"
metadata:
  created_at: "2025-11-01T00:00:00Z"
work_plans:
  - id: plan-test
    name: "Test Plan"
    depends_on: []
    todos:
      - id: "1"
        title: "Task 1"
        status: pending
    references: []
""")

    # when
    result = runner.invoke(app, ["plan", "export", "test.yaml", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Task 1" in result.stdout


def test_task_show__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
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
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
    current_task_id: "1"
  progress:
    total_tasks: 1
    completed: 0
    in_progress: 0
    pending: 1
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Task 1"
    status: pending
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
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

    # when
    result = runner.invoke(app, ["task", "show", "1", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Task 1" in result.stdout


def test_task_current__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
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
status:
  execution:
    started: false
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
    title: "Task 1"
    status: in_progress
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
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

    # when
    result = runner.invoke(app, ["task", "current", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Task 1" in result.stdout


def test_task_next__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()
    yaml_file = cwd_dir / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
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
status:
  execution:
    started: false
    completed: false
  work_mode:
    parallel_requested: false
  progress:
    total_tasks: 2
    completed: 1
    in_progress: 0
    pending: 1
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Task 1"
    status: completed
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
    references: []
    children: []
    verification_spec: []
  - id: "2"
    title: "Task 2"
    status: pending
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
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

    # when
    result = runner.invoke(app, ["task", "next", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 0
    assert "Task 2" in result.stdout


def test_task_continue__with_cwd_option__resolves_path(tmp_path: Path) -> None:
    # given
    cwd_dir = tmp_path / "subdir"
    cwd_dir.mkdir()

    # when
    result = runner.invoke(app, ["task", "continue", "--cwd", str(cwd_dir)])

    # then
    assert result.exit_code == 1
    assert "Working directory:" in result.stdout
    assert "subdir" in result.stdout


def test_resolve_cwd__with_none__returns_current_directory() -> None:
    # given
    from sisyphus.cli.common import resolve_cwd

    # when
    result = resolve_cwd(None)

    # then
    assert result == Path.cwd()


def test_resolve_cwd__with_relative_path__converts_to_absolute(tmp_path: Path) -> None:
    # given
    import os

    from sisyphus.cli.common import resolve_cwd

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # when
        result = resolve_cwd("subdir")

        # then
        assert result.is_absolute()
        assert result == subdir
    finally:
        os.chdir(original_cwd)


def test_resolve_cwd__with_absolute_path__returns_as_is(tmp_path: Path) -> None:
    # given
    from sisyphus.cli.common import resolve_cwd

    # when
    result = resolve_cwd(str(tmp_path))

    # then
    assert result == tmp_path


def test_cwd_option__with_nonexistent_directory__command_handles_gracefully(tmp_path: Path) -> None:
    # given
    nonexistent = tmp_path / "nonexistent"

    # when
    result = runner.invoke(app, ["plan", "lint", "--file", "test.yaml", "--cwd", str(nonexistent)])

    # then
    assert result.exit_code != 0
