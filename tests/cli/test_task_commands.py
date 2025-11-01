from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.commands.task import task_app

pytestmark = [pytest.mark.anyio]

runner = CliRunner()


def test_show__with_valid_task_id__displays_task(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
    yaml_content = """metadata:
  created_at: "2025-01-01T00:00:00Z"
  updated_at: "2025-01-01T00:00:00Z"
user_request:
  original: "Test request"
  created_at: "2025-01-01T00:00:00Z"
  additional: []
objectives:
  core: "Test objective"
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
    title: "Test Task"
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
    result = runner.invoke(task_app, ["show", "1", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "Test Task" in result.stdout


def test_show__with_invalid_task_id__fails(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
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
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["show", "999", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 1
    assert "작업 ID를 찾을 수 없습니다" in result.stdout


def test_current__with_in_progress_task__displays_task(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
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
    title: "Current Task"
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
    result = runner.invoke(task_app, ["current", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "Current Task" in result.stdout


def test_current__with_no_task_started__returns_message(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
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
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["current", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "작업이 시작되지 않았습니다" in result.stdout


def test_next__with_pending_task__displays_task(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
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
    total_tasks: 1
    completed: 0
    in_progress: 0
    pending: 1
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Next Task"
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
    result = runner.invoke(task_app, ["next", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "Next Task" in result.stdout


def test_next__with_all_completed__returns_message(tmp_path: Path) -> None:
    # given
    yaml_file = tmp_path / "ai-todolist.yaml"
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
    started: true
    completed: true
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
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["next", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "모든 작업이 완료되었습니다" in result.stdout


def test_continue__shows_not_implemented_message(tmp_path: Path) -> None:
    # given - when
    result = runner.invoke(task_app, ["continue", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 1
    assert "not yet implemented" in result.stdout
