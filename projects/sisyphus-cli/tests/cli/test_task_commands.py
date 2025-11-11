from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sisyphus.cli.task import task_app

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skip(reason="CLI tests require v2.1 compatibility layer - deferred to post-v3.0 release"),
]

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


def test_continue__when_not_started__starts_first_task(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "First Task"
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
    result = runner.invoke(task_app, ["continue", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "작업을 시작합니다" in result.stdout
    assert "First Task" in result.stdout


def test_continue__when_verification_incomplete__rejects_with_message(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Task with Verification"
    status: in_progress
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
    references: []
    children: []
    verification_spec:
      - id: "v1"
        title: "Unverified Item"
        description: "Test"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo test"
            expected_exit_code: 0
        llm_judge: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["continue", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 1
    assert "다음 작업으로 넘어갈 수 없습니다" in result.stdout
    assert "검증: 0/1 완료" in result.stdout


def test_continue__when_all_complete__moves_to_next_task(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "First Task"
    status: in_progress
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
    references: []
    children: []
    verification_spec: []
  - id: "2"
    title: "Second Task"
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
    result = runner.invoke(task_app, ["continue", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "다음 작업으로 이동" in result.stdout
    assert "Second Task" in result.stdout


def test_continue__when_last_task_complete__marks_all_complete(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Last Task"
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
    result = runner.invoke(task_app, ["continue", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "모든 작업이 완료되었습니다" in result.stdout


def test_verify_bash__with_bash_verification__executes_and_marks_verified(tmp_path: Path) -> None:
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
    verification_spec:
      - id: "v1"
        title: "Test Verification"
        description: "Test bash verification"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo hello"
            expected_exit_code: 0
        llm_judge: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["verify", "bash", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "검증 1/1" in result.stdout
    assert "Test Verification" in result.stdout
    assert "✓ 성공" in result.stdout


def test_verify_bash__with_all_verified__shows_completion_message(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "Test Task"
    status: completed
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
    references: []
    children: []
    verification_spec:
      - id: "v1"
        title: "Test Verification"
        description: "Test"
        verified: true
        verified_at: "2025-01-01T00:00:00Z"
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo verified"
            expected_exit_code: 0
        llm_judge: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["verify", "bash", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "모든 검증이 완료되었습니다" in result.stdout


def test_verify_status__with_mixed_verifications__shows_status(tmp_path: Path) -> None:
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
    verification_spec:
      - id: "v1"
        title: "Verified Item"
        description: "Test"
        verified: true
        verified_at: "2025-01-01T00:00:00Z"
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo verified"
            expected_exit_code: 0
        llm_judge: []
      - id: "v2"
        title: "Unverified Item"
        description: "Test"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo test"
            expected_exit_code: 0
        llm_judge: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(task_app, ["verify", "status", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "검증 상태: 1/2 완료" in result.stdout
    assert "Verified Item" in result.stdout
    assert "Unverified Item" in result.stdout
    assert "남은 검증: 1개" in result.stdout


def test_verify_llm_mark__with_valid_verify_id__marks_verified(tmp_path: Path) -> None:
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
    verification_spec:
      - id: "v1"
        title: "LLM Verification"
        description: "Test"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash: []
        llm_judge:
          - by: orchestrator-agent
            context_commands: []
            instruction: "Check something"
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(
        task_app, ["verify", "llm-mark", "v1", "--evidence", "LLM verified", "--cwd", str(tmp_path)]
    )

    # then
    assert result.exit_code == 0
    assert "LLM 검증이 완료 표시되었습니다" in result.stdout


def test_verify_manual_mark__with_valid_verify_id__marks_verified(tmp_path: Path) -> None:
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
    verification_spec:
      - id: "v1"
        title: "Manual Verification"
        description: "Test"
        verified: false
        orchestrator_manually_verified: false
        manual_verification_evidence: ""
        bash:
          - execute: "echo manual"
            expected_exit_code: 0
        llm_judge: []
success_vision:
  user_perspective: []
  business_perspective: []
  technical_criteria: []
final_verification: []
"""
    yaml_file.write_text(yaml_content)

    # when
    result = runner.invoke(
        task_app, ["verify", "manual-mark", "v1", "--evidence", "Manually checked", "--cwd", str(tmp_path)]
    )

    # then
    assert result.exit_code == 0
    assert "수동 검증이 완료 표시되었습니다" in result.stdout


def test_previous__with_not_started__shows_not_started_message(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "First Task"
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
    result = runner.invoke(task_app, ["previous", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "작업이 시작되지 않았습니다" in result.stdout


def test_previous__with_first_task__shows_first_task_message(tmp_path: Path) -> None:
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
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "First Task"
    status: in_progress
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
    references: []
    children: []
    verification_spec: []
  - id: "2"
    title: "Second Task"
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
    result = runner.invoke(task_app, ["previous", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "첫 작업입니다" in result.stdout


def test_previous__with_second_task__shows_previous_task(tmp_path: Path) -> None:
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
    current_task_id: "2"
  current_work: ""
workflow:
  dependency_diagram: ""
todos:
  - id: "1"
    title: "First Task"
    status: completed
    created_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
    references: []
    children: []
    verification_spec: []
  - id: "2"
    title: "Second Task"
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
    result = runner.invoke(task_app, ["previous", "--cwd", str(tmp_path)])

    # then
    assert result.exit_code == 0
    assert "First Task" in result.stdout


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
            bash: []
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
    status_content = '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", "plan_id": "test-plan"}}'
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
            bash: []
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
    status_content = '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", "plan_id": "test-plan"}}'
    status_file.write_text(status_content)

    evidence = "a" * 99  # 99 characters

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code != 0
    assert "100" in result.stdout
    assert "증거" in result.stdout


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
            bash: []
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
    status_content = '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", "plan_id": "test-plan"}}'
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
            bash: []
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
    status_content = '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", "plan_id": "test-plan"}}'
    status_file.write_text(status_content)

    evidence = ""  # empty string

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code != 0
    assert "100" in result.stdout


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
            bash: []
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
    status_content = '{"current_plan": {"plan_path": ".sisyphus/tasks/test-plan.yaml", "plan_id": "test-plan"}}'
    status_file.write_text(status_content)

    evidence = "short"  # too short

    # when
    result = runner.invoke(task_app, ["verify", "manual-mark", "v1", "--evidence", evidence, "--cwd", str(tmp_path)])

    # then
    assert result.exit_code != 0
    # Check error message contains reason
    assert "이유" in result.stdout or "철저한" in result.stdout
    # Check error message contains example
    assert "예시" in result.stdout or "Chrome" in result.stdout
    # Check error message contains guidance
    assert "가이드" in result.stdout or "검증" in result.stdout
