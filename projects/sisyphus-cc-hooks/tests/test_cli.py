# pyright: reportMissingImports=false
import json
import subprocess
from pathlib import Path

import pytest
import typer

from sisyphus_cc_hooks.cli import app, post_tool_use


def test_cli_module_import__succeeds() -> None:
    # given: CLI module
    # when: Import app and command
    # then: No import errors
    assert app is not None
    assert post_tool_use is not None


def test_post_tool_use_command__with_executor_agent__exits_with_code_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # given: YAML plan with task in progress
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos:
      - id: task-1
        title: "Test Task"
        status: in_progress
        verification_spec: []
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(
        json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}})
    )

    json_input = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # Mock stdin
    mock_stdin = type("", (), {"read": lambda self: json.dumps(json_input)})()
    monkeypatch.setattr("sys.stdin", mock_stdin)

    # when: Call post_tool_use directly
    # then: Exits with code 2
    with pytest.raises(typer.Exit) as exc_info:
        post_tool_use()
    assert exc_info.value.exit_code == 2


def test_cli_post_tool_use_command__with_valid_input__executes_hook(
    tmp_path: Path,
) -> None:
    # given: YAML plan with task in progress
    sisyphus_dir = tmp_path / ".sisyphus"
    sisyphus_dir.mkdir()
    tasks_dir = sisyphus_dir / "tasks"
    tasks_dir.mkdir()

    plan_file = tasks_dir / "test.yaml"
    plan_file.write_text("""work_plans:
  - id: test-plan
    todos:
      - id: task-1
        title: "Test Task"
        status: in_progress
        verification_spec: []
    work_mode:
      current_task_id: task-1
""")

    status_file = sisyphus_dir / "status.json"
    status_file.write_text(
        json.dumps({"current_plan": {"plan_path": ".sisyphus/tasks/test.yaml"}})
    )

    json_input = {
        "tool_input": {"subagent_type": "sisyphus-executor"},
        "cwd": str(tmp_path),
        "session_id": "test",
    }

    # when: Execute CLI command
    proc = subprocess.run(
        ["uv", "run", "sisyphus-cc-hooks"],
        input=json.dumps(json_input),
        capture_output=True,
        text=True,
        check=False,
    )

    # then: Hook executes and outputs message
    assert proc.returncode == 2
    assert "EXECUTOR TASK COMPLETION DETECTED" in proc.stderr
    assert "[ALL VERIFICATIONS COMPLETED]" in proc.stderr


def test_cli_help__displays_usage() -> None:
    # when
    proc = subprocess.run(
        ["uv", "run", "sisyphus-cc-hooks", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    # then
    assert proc.returncode == 0
    assert "sisyphus-cc-hooks" in proc.stdout
    assert "post-tool-use" in proc.stdout
